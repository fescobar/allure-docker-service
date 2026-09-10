package projects

import (
	"bytes"
	"errors"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

func TestValidateProjectID(t *testing.T) {
	tests := []struct {
		name    string
		id      string
		wantErr bool
	}{
		// valid basic
		{"numeric", "1234567890", false},
		{"single digit", "1", false},
		{"single letter", "a", false},
		{"word", "demo", false},
		{"default", "default", false},

		// valid separators inside
		{"hyphen inside", "my-project", false},
		{"underscore inside", "my_project", false},
		{"space inside", "my project", false},
		{"mixed separators", "my_project-1 demo", false},
		{"leading zeros", "000123", false},

		// length boundaries
		{"length 199", strings.Repeat("a", 199), false},
		{"length 200", strings.Repeat("a", 200), false},
		{"length 201", strings.Repeat("a", 201), true},

		// invalid empty
		{"empty", "", true},

		// invalid start
		{"leading hyphen", "-abc", true},
		{"leading underscore", "_abc", true},
		{"leading space", " abc", true},

		// invalid end
		{"trailing hyphen", "abc-", true},
		{"trailing underscore", "abc_", true},
		{"trailing space", "abc ", true},

		// invalid characters
		{"uppercase letters", "ABC123", true},
		{"tab", "abc\t123", true},
		{"newline", "abc\n123", true},
		{"plus sign", "abc+123", true},
		{"dot", "abc.123", true},
		{"slash", "abc/123", true},
		{"backslash", `abc\123`, true},
		{"path traversal", "../abc", true},
		{"unicode digits", "１２３", true},
		{"emoji", "abc😀123", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateProjectID(tt.id)

			if tt.wantErr {
				if err == nil {
					t.Fatalf("ValidateProjectID(%q) error = nil, want error", tt.id)
				}
				return
			}

			if err != nil {
				t.Fatalf("ValidateProjectID(%q) error = %v, want nil", tt.id, err)
			}
		})
	}
}

func TestSanitizeResultFileName(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		want    string
		wantErr bool
	}{
		// valid names
		{"simple json", "8f2c-result.json", "8f2c-result.json", false},
		{"letters digits dot dash underscore", "abc_123-test.json", "abc_123-test.json", false},
		{"single character", "a", "a", false},
		{"max length 255", strings.Repeat("a", 255), strings.Repeat("a", 255), false},

		// filepath.Base sanitization
		{"unix traversal", "../../etc/passwd", "passwd", false},
		{"unix nested path", "dir/sub/file.json", "file.json", false},
		{"trailing slash", "dir/", "dir", false},

		// hidden and dot-only names allowed by current regexp
		{"hidden file", ".hidden.json", ".hidden.json", false},
		{"many dots", "....", "....", false},

		// platform-dependent backslash handling on Unix
		{"windows traversal on unix", `..\..\etc\passwd`, "", true},
		{"windows style path on unix", `dir\sub\file.json`, "", true},

		// unsafe names
		{"empty", "", "", true},
		{"dot", ".", "", true},
		{"dot dot", "..", "", true},
		{"path separator", string(filepath.Separator), "", true},

		// too long
		{"length 256", strings.Repeat("a", 256), "", true},

		// invalid characters
		{"space", "rep ort.json", "", true},
		{"tab", "rep\tort.json", "", true},
		{"newline", "rep\nort.json", "", true},
		{"plus", "rep+ort.json", "", true},
		{"colon", "rep:ort.json", "", true},
		{"backslash", `rep\ort.json`, "", true},
		{"unicode", "отчет.json", "", true},
		{"emoji", "report😀.json", "", true},
		{"asterisk", "report*.json", "", true},
		{"question mark", "report?.json", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := SanitizeResultFileName(tt.input)

			if tt.wantErr {
				if err == nil {
					t.Fatalf("SanitizeResultFileName(%q) error = nil, want error", tt.input)
				}
				return
			}

			if err != nil {
				t.Fatalf("SanitizeResultFileName(%q) error = %v, want nil", tt.input, err)
			}

			if got != tt.want {
				t.Fatalf("SanitizeResultFileName(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}

func ExampleSanitizeResultFileName() {
	for _, in := range []string{
		"8f2c-result.json",
		"../../etc/passwd",
		"..",
		"rep ort.json",
	} {
		name, err := SanitizeResultFileName(in)
		fmt.Printf("%q -> %q, %v\n", in, name, err)
	}

	// Output:
	// "8f2c-result.json" -> "8f2c-result.json", <nil>
	// "../../etc/passwd" -> "passwd", <nil>
	// ".." -> "", unsafe file name ".."
	// "rep ort.json" -> "", invalid character in file name: "rep ort.json"
}

func TestCreateDir(t *testing.T) {
	t.Run("creates reports and results", func(t *testing.T) {
		base := t.TempDir()

		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("CreateDir(base, %q) returned unexpected error: %v", "demo", err)
		}

		for _, dir := range []string{ReportsDir(base, "demo"), ResultsDir(base, "demo")} {
			info, err := os.Stat(dir)
			if err != nil {
				t.Errorf("stat %q: %v", dir, err)
				continue
			}
			if !info.IsDir() {
				t.Errorf("%q exists but is not a directory", dir)
			}
		}
	})

	t.Run("existing project reports ErrProjectExists", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("first CreateDir returned unexpected error: %v", err)
		}

		err := CreateDir(base, "demo")
		if !errors.Is(err, ErrProjectExists) {
			t.Fatalf("second CreateDir error = %v, want ErrProjectExists", err)
		}
	})

	t.Run("plain file in place of project dir reports ErrProjectExists", func(t *testing.T) {
		base := t.TempDir()
		if err := os.WriteFile(filepath.Join(base, "demo"), nil, 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		err := CreateDir(base, "demo")
		if !errors.Is(err, ErrProjectExists) {
			t.Fatalf("CreateDir error = %v, want ErrProjectExists", err)
		}
	})

	t.Run("missing base dir fails without creating anything", func(t *testing.T) {
		base := filepath.Join(t.TempDir(), "does-not-exist")

		err := CreateDir(base, "demo")
		if err == nil {
			t.Fatal("CreateDir with a missing base dir returned nil, want error")
		}
		if errors.Is(err, ErrProjectExists) {
			t.Fatalf("CreateDir error = %v, want a filesystem error", err)
		}
		if _, err := os.Stat(base); !errors.Is(err, os.ErrNotExist) {
			t.Errorf("base dir %q was created, want it left alone", base)
		}
	})
}

func TestClearResults(t *testing.T) {
	t.Run("removes top-level files, leaves subdirectories", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}
		results := ResultsDir(base, "demo")
		if err := os.WriteFile(filepath.Join(results, "a-result.json"), []byte("{}"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(filepath.Join(results, "b-result.json"), []byte("{}"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		sub := filepath.Join(results, "kept-dir")
		if err := os.MkdirAll(sub, 0755); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(filepath.Join(sub, "inside.json"), []byte("{}"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := ClearResults(base, "demo"); err != nil {
			t.Fatalf("ClearResults returned unexpected error: %v", err)
		}

		entries, err := os.ReadDir(results)
		if err != nil {
			t.Fatalf("ReadDir after ClearResults: %v", err)
		}
		if len(entries) != 1 || entries[0].Name() != "kept-dir" {
			t.Fatalf("results dir after ClearResults = %v, want only kept-dir", entries)
		}
		if _, err := os.Stat(filepath.Join(sub, "inside.json")); err != nil {
			t.Errorf("file inside kept-dir was removed: %v", err)
		}
	})

	t.Run("already-empty results directory succeeds", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := ClearResults(base, "demo"); err != nil {
			t.Fatalf("ClearResults on empty results returned unexpected error: %v", err)
		}
	})

	t.Run("missing results directory reports the error", func(t *testing.T) {
		base := t.TempDir()

		err := ClearResults(base, "nosuch")
		if !errors.Is(err, os.ErrNotExist) {
			t.Fatalf("ClearResults error = %v, want it to wrap fs.ErrNotExist", err)
		}
	})
}

func TestClearHistory(t *testing.T) {
	// writeArchive creates <baseDir>/<id>/reports/<name>/index.html so an
	// archive is a non-empty directory, the same shape a real build leaves -
	// os.Remove refuses to delete a directory that isn't empty, so a test
	// against an empty one would not catch that mistake.
	writeArchive := func(t *testing.T, base, id, name string) {
		t.Helper()
		dir := filepath.Join(ReportsDir(base, id), name)
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(filepath.Join(dir, "index.html"), []byte("<h1>"+name+"</h1>"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
	}

	t.Run("removes numbered archives, leaves latest and non-numeric entries", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}
		writeArchive(t, base, "demo", "latest")
		writeArchive(t, base, "demo", "1")
		writeArchive(t, base, "demo", "2")
		if err := os.WriteFile(filepath.Join(ReportsDir(base, "demo"), "notes.txt"), nil, 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := ClearHistory(base, "demo"); err != nil {
			t.Fatalf("ClearHistory returned unexpected error: %v", err)
		}

		for _, kept := range []string{"latest", "notes.txt"} {
			if _, err := os.Stat(filepath.Join(ReportsDir(base, "demo"), kept)); err != nil {
				t.Errorf("%q was removed, want it kept: %v", kept, err)
			}
		}
		for _, gone := range []string{"1", "2"} {
			if _, err := os.Stat(filepath.Join(ReportsDir(base, "demo"), gone)); !errors.Is(err, os.ErrNotExist) {
				t.Errorf("archive %q still exists, want it removed (stat err = %v)", gone, err)
			}
		}
	})

	t.Run("removes history file and executor.json", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(HistoryFile(base, "demo"), []byte(`{"n":1}`), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		executor := filepath.Join(ResultsDir(base, "demo"), ExecutorFileName)
		if err := os.WriteFile(executor, []byte(`{"buildOrder":5}`), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := ClearHistory(base, "demo"); err != nil {
			t.Fatalf("ClearHistory returned unexpected error: %v", err)
		}

		if _, err := os.Stat(HistoryFile(base, "demo")); !errors.Is(err, os.ErrNotExist) {
			t.Errorf("history file still exists (stat err = %v)", err)
		}
		if _, err := os.Stat(executor); !errors.Is(err, os.ErrNotExist) {
			t.Errorf("executor.json still exists (stat err = %v)", err)
		}
	})

	t.Run("fresh project with nothing to clear succeeds", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := ClearHistory(base, "demo"); err != nil {
			t.Fatalf("ClearHistory on a fresh project returned unexpected error: %v", err)
		}
	})

	t.Run("missing reports directory reports the error", func(t *testing.T) {
		base := t.TempDir()

		err := ClearHistory(base, "nosuch")
		if !errors.Is(err, os.ErrNotExist) {
			t.Fatalf("ClearHistory error = %v, want it to wrap fs.ErrNotExist", err)
		}
	})
}

// TestHistoryFileStaysOutOfResults guards the one property of the history
// path that is not a matter of taste. Every build appends to this file, and
// the watcher rebuilds a project whenever the listing of its results
// directory changes — put the two together and each build schedules the next
// one, forever. Moving the file under ResultsDir compiles, passes every other
// test, and only shows up in production as a project that rebuilds itself in
// a loop.
func TestHistoryFileStaysOutOfResults(t *testing.T) {
	base := t.TempDir()

	history := HistoryFile(base, "demo")
	results := ResultsDir(base, "demo") + string(filepath.Separator)

	if strings.HasPrefix(history, results) {
		t.Errorf("HistoryFile = %q, want it outside the results dir %q", history, results)
	}
}

func TestCleanTmp(t *testing.T) {
	// stageTmp creates <base>/<id>/.tmp/build-1/index.html, the shape a build
	// killed mid-flight leaves behind: a non-empty nested directory, which
	// os.Remove would refuse to delete.
	stageTmp := func(t *testing.T, base, id string) string {
		t.Helper()
		tmp := TmpRoot(base, id)
		dir := filepath.Join(tmp, "build-1")
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(filepath.Join(dir, "index.html"), []byte("<h1>stale</h1>"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		return tmp
	}

	// captureLog redirects the standard logger into a buffer for the length of
	// one subtest. CleanTmp reports a project it could not clean by logging,
	// so the log is the only place that behaviour is observable.
	captureLog := func(t *testing.T) *bytes.Buffer {
		t.Helper()
		var buf bytes.Buffer
		log.SetOutput(&buf)
		t.Cleanup(func() { log.SetOutput(os.Stderr) })
		return &buf
	}

	t.Run("removes .tmp from every project", func(t *testing.T) {
		base := t.TempDir()
		var staged []string
		for _, id := range []string{"alpha", "beta", "gamma"} {
			if err := CreateDir(base, id); err != nil {
				t.Fatalf("setup: %v", err)
			}
			staged = append(staged, stageTmp(t, base, id))
		}
		// ReadDir returns entries sorted by name, and an uppercase R sorts
		// before a lowercase a: this file is seen before any project, so a
		// sweep that stops at the first non-project instead of skipping it
		// cleans nothing at all.
		if err := os.WriteFile(filepath.Join(base, "README.txt"), []byte("not a project"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := CleanTmp(base); err != nil {
			t.Fatalf("CleanTmp returned unexpected error: %v", err)
		}

		for _, tmp := range staged {
			if _, err := os.Stat(tmp); !errors.Is(err, os.ErrNotExist) {
				t.Errorf("%q still exists after CleanTmp (stat error = %v)", tmp, err)
			}
		}
	})

	t.Run("leaves results and reports untouched", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}
		stageTmp(t, base, "demo")
		result := filepath.Join(ResultsDir(base, "demo"), "a-result.json")
		if err := os.WriteFile(result, []byte("{}"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		published := filepath.Join(LatestReportDir(base, "demo"), "index.html")
		if err := os.MkdirAll(LatestReportDir(base, "demo"), 0755); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if err := os.WriteFile(published, []byte("<h1>report</h1>"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := CleanTmp(base); err != nil {
			t.Fatalf("CleanTmp returned unexpected error: %v", err)
		}

		for _, path := range []string{result, published} {
			if _, err := os.Stat(path); err != nil {
				t.Errorf("CleanTmp removed %q: %v", path, err)
			}
		}
	})

	t.Run("a project without .tmp is not an error", func(t *testing.T) {
		base := t.TempDir()
		if err := CreateDir(base, "demo"); err != nil {
			t.Fatalf("setup: %v", err)
		}

		if err := CleanTmp(base); err != nil {
			t.Fatalf("CleanTmp returned unexpected error: %v", err)
		}
		if _, err := os.Stat(ProjectDir(base, "demo")); err != nil {
			t.Errorf("project directory disappeared: %v", err)
		}
	})

	t.Run("empty projects directory is not an error", func(t *testing.T) {
		if err := CleanTmp(t.TempDir()); err != nil {
			t.Fatalf("CleanTmp on empty root returned unexpected error: %v", err)
		}
	})

	t.Run("skips files and directories that are not projects", func(t *testing.T) {
		base := t.TempDir()
		loose := filepath.Join(base, "README.txt")
		if err := os.WriteFile(loose, []byte("not a project"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		// Uppercase and a leading dot both fail ValidateProjectID, so these
		// directories were not created by this service. Their .tmp must
		// survive: sweeping them would mean deleting a stranger's data.
		// A regular file whose name is a valid project ID: the name passes
		// ValidateProjectID, so only the IsDir check keeps CleanTmp from
		// trying to remove <base>/alpha/.tmp and logging about it.
		if err := os.WriteFile(filepath.Join(base, "alpha"), []byte("not a project"), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
		foreign := []string{"NotAProject", ".hidden"}
		var kept []string
		for _, name := range foreign {
			dir := filepath.Join(base, name, ".tmp")
			if err := os.MkdirAll(dir, 0755); err != nil {
				t.Fatalf("setup: %v", err)
			}
			kept = append(kept, dir)
		}

		logged := captureLog(t)
		if err := CleanTmp(base); err != nil {
			t.Fatalf("CleanTmp returned unexpected error: %v", err)
		}

		if logged.Len() != 0 {
			t.Errorf("CleanTmp logged about a non-project entry: %s", logged.String())
		}
		if _, err := os.Stat(loose); err != nil {
			t.Errorf("CleanTmp removed a loose file: %v", err)
		}
		for _, dir := range kept {
			if _, err := os.Stat(dir); err != nil {
				t.Errorf("CleanTmp removed %q, which is not a project: %v", dir, err)
			}
		}
	})

	t.Run("a project that cannot be cleaned does not stop the sweep", func(t *testing.T) {
		if os.Geteuid() == 0 {
			t.Skip("root ignores directory permissions")
		}
		base := t.TempDir()
		for _, id := range []string{"alpha", "beta"} {
			if err := CreateDir(base, id); err != nil {
				t.Fatalf("setup: %v", err)
			}
			stageTmp(t, base, id)
		}
		// Removing .tmp means unlinking an entry from its parent, so it is the
		// project directory that has to lose write permission, not .tmp
		// itself. alpha sorts first, so the failure happens before beta is
		// reached. Restored in cleanup, or t.TempDir cannot delete the tree.
		locked := ProjectDir(base, "alpha")
		if err := os.Chmod(locked, 0500); err != nil {
			t.Fatalf("setup: %v", err)
		}
		t.Cleanup(func() {
			if err := os.Chmod(locked, 0755); err != nil {
				t.Errorf("cleanup: restoring permissions on %q: %v", locked, err)
			}
		})

		logged := captureLog(t)
		if err := CleanTmp(base); err != nil {
			t.Fatalf("CleanTmp returned an error for one unremovable project: %v", err)
		}

		if !strings.Contains(logged.String(), TmpRoot(base, "alpha")) {
			t.Errorf("CleanTmp did not log the project it could not clean, log = %q", logged.String())
		}
		if _, err := os.Stat(TmpRoot(base, "beta")); !errors.Is(err, os.ErrNotExist) {
			t.Errorf("beta was not cleaned after alpha failed (stat error = %v)", err)
		}
	})

	t.Run("missing projects directory reports the error", func(t *testing.T) {
		err := CleanTmp(filepath.Join(t.TempDir(), "nosuch"))
		if !errors.Is(err, os.ErrNotExist) {
			t.Fatalf("CleanTmp error = %v, want it to wrap fs.ErrNotExist", err)
		}
	})
}

func TestSeedHistory(t *testing.T) {
	// seedProject creates a project and, when content is not empty, gives it a
	// history file holding exactly that. An empty string means the project
	// exists but has never been built, which is the state the empty-source
	// branch is about.
	seedProject := func(t *testing.T, base, id, content string) {
		t.Helper()
		if err := CreateDir(base, id); err != nil {
			t.Fatalf("setup: %v", err)
		}
		if content == "" {
			return
		}
		if err := os.WriteFile(HistoryFile(base, id), []byte(content), 0644); err != nil {
			t.Fatalf("setup: %v", err)
		}
	}

	// projectFiles lists the names directly under a project directory.
	// SeedHistory stages through a scratch file beside the destination, and
	// nothing cleans that up later - Generate only clears TmpRoot - so a
	// leftover is a leak that lives for the life of the volume. Comparing
	// listings catches one under any name; asserting on the scratch name
	// itself would only catch the name this test already guessed.
	projectFiles := func(t *testing.T, base, id string) []string {
		t.Helper()
		entries, err := os.ReadDir(ProjectDir(base, id))
		if err != nil {
			t.Fatalf("failed to read project dir: %v", err)
		}
		names := make([]string, 0, len(entries))
		for _, entry := range entries {
			names = append(names, entry.Name())
		}
		return names
	}

	t.Run("copies the source history over the target's own", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "{\"run\":1}\n{\"run\":2}\n")
		seedProject(t, base, "dst", "{\"stale\":true}\n")

		if err := SeedHistory(base, "dst", "src"); err != nil {
			t.Fatalf("SeedHistory returned unexpected error: %v", err)
		}

		got, err := os.ReadFile(HistoryFile(base, "dst"))
		if err != nil {
			t.Fatalf("reading the seeded history: %v", err)
		}
		want := "{\"run\":1}\n{\"run\":2}\n"
		if string(got) != want {
			t.Errorf("seeded history = %q, want %q", got, want)
		}
	})

	t.Run("leaves the source history untouched", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "{\"run\":1}\n")
		seedProject(t, base, "dst", "")

		if err := SeedHistory(base, "dst", "src"); err != nil {
			t.Fatalf("SeedHistory returned unexpected error: %v", err)
		}

		got, err := os.ReadFile(HistoryFile(base, "src"))
		if err != nil {
			t.Fatalf("reading the source history: %v", err)
		}
		if string(got) != "{\"run\":1}\n" {
			t.Errorf("source history = %q, want it unchanged", got)
		}
	})

	t.Run("target with no history of its own is seeded", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "{\"run\":1}\n")
		seedProject(t, base, "dst", "")

		if err := SeedHistory(base, "dst", "src"); err != nil {
			t.Fatalf("SeedHistory returned unexpected error: %v", err)
		}

		if _, err := os.Stat(HistoryFile(base, "dst")); err != nil {
			t.Errorf("target has no history after seeding: %v", err)
		}
	})

	// The empty-source case is the one the postcondition is easiest to get
	// wrong in: returning early on "nothing to copy" leaves the target holding
	// a history the source does not have, and the next build then compares the
	// target against its own previous run - the very comparison seeding is
	// there to replace.
	t.Run("source without history clears the target and reports ErrNoHistory", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "")
		seedProject(t, base, "dst", "{\"stale\":true}\n")

		err := SeedHistory(base, "dst", "src")
		if !errors.Is(err, ErrNoHistory) {
			t.Fatalf("SeedHistory error = %v, want ErrNoHistory", err)
		}

		if _, err := os.Stat(HistoryFile(base, "dst")); !errors.Is(err, os.ErrNotExist) {
			t.Errorf("target history survived an empty source (stat err = %v)", err)
		}
	})

	t.Run("neither project has history and it still reports ErrNoHistory", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "")
		seedProject(t, base, "dst", "")

		err := SeedHistory(base, "dst", "src")
		if !errors.Is(err, ErrNoHistory) {
			t.Fatalf("SeedHistory error = %v, want ErrNoHistory", err)
		}
	})

	// A missing target must not be answered with ErrNoHistory: that error
	// sends the caller looking at the source project, which is fine, while the
	// real fault is a target that does not exist at all.
	t.Run("missing target project reports fs.ErrNotExist, not ErrNoHistory", func(t *testing.T) {
		base := t.TempDir()

		for _, sourceHistory := range []string{"{\"run\":1}\n", ""} {
			srcID := fmt.Sprintf("src-%d", len(sourceHistory))
			seedProject(t, base, srcID, sourceHistory)

			err := SeedHistory(base, "nosuch", srcID)
			if !errors.Is(err, os.ErrNotExist) {
				t.Errorf("source history %q: error = %v, want it to wrap fs.ErrNotExist",
					sourceHistory, err)
			}
			if errors.Is(err, ErrNoHistory) {
				t.Errorf("source history %q: error = %v, want the missing target reported instead",
					sourceHistory, err)
			}
		}
	})

	t.Run("missing source project reports ErrNoHistory", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "dst", "")

		err := SeedHistory(base, "dst", "nosuch")
		if !errors.Is(err, ErrNoHistory) {
			t.Fatalf("SeedHistory error = %v, want ErrNoHistory", err)
		}
	})

	t.Run("leaves no staging file behind", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "{\"run\":1}\n")
		seedProject(t, base, "dst", "")

		before := projectFiles(t, base, "dst")

		if err := SeedHistory(base, "dst", "src"); err != nil {
			t.Fatalf("SeedHistory returned unexpected error: %v", err)
		}

		want := append(slices.Clone(before), "history.jsonl")
		slices.Sort(want)
		got := projectFiles(t, base, "dst")
		slices.Sort(got)
		if !slices.Equal(got, want) {
			t.Errorf("project directory holds %v, want %v", got, want)
		}
	})

	// Seeding a project from itself would succeed and change nothing, so the
	// refusal is about the arrangement, not the file: a project measured
	// against its own previous build is exactly what seeding replaces.
	t.Run("refuses to seed a project from itself", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "dst", "{\"own\":true}\n")

		err := SeedHistory(base, "dst", "dst")

		if !errors.Is(err, ErrCopyToSelf) {
			t.Fatalf("SeedHistory returned %v, want ErrCopyToSelf", err)
		}
		got, readErr := os.ReadFile(HistoryFile(base, "dst"))
		if readErr != nil {
			t.Fatalf("the refusal touched the history file: %v", readErr)
		}
		if string(got) != "{\"own\":true}\n" {
			t.Errorf("history = %q, want it untouched", got)
		}
	})

	// The deferred cleanup only earns its keep when the rename fails: on the
	// happy path the rename moves the staging file away by itself. A
	// directory sitting where the history file belongs is the cheapest way
	// to make rename(2) refuse.
	t.Run("leaves no staging file behind when the rename fails", func(t *testing.T) {
		base := t.TempDir()
		seedProject(t, base, "src", "{\"run\":1}\n")
		seedProject(t, base, "dst", "")

		blocker := HistoryFile(base, "dst")
		if err := os.MkdirAll(filepath.Join(blocker, "occupied"), 0o755); err != nil {
			t.Fatalf("failed to block the destination: %v", err)
		}

		before := projectFiles(t, base, "dst")

		if err := SeedHistory(base, "dst", "src"); err == nil {
			t.Fatal("SeedHistory returned nil, want the rename to fail")
		}

		want := slices.Clone(before)
		slices.Sort(want)
		got := projectFiles(t, base, "dst")
		slices.Sort(got)
		if !slices.Equal(got, want) {
			t.Errorf("project directory holds %v, want %v", got, want)
		}
	})

	// Both IDs reach filepath.Join, so an unvalidated one climbs out of
	// baseDir. The target is the dangerous half - it is written to and
	// removed - but a source that escapes reads a file it has no business
	// reading, so both are checked.
	t.Run("rejects invalid IDs without touching the filesystem", func(t *testing.T) {
		tests := []struct {
			name         string
			target, from string
		}{
			{"target escapes", "../evil", "src"},
			{"source escapes", "dst", "../evil"},
			{"target empty", "", "src"},
			{"source empty", "dst", ""},
			{"target uppercase", "DST", "src"},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				base := t.TempDir()
				outside := filepath.Join(base, "..", "evil")
				seedProject(t, base, "src", "{\"run\":1}\n")
				seedProject(t, base, "dst", "{\"stale\":true}\n")

				err := SeedHistory(base, tt.target, tt.from)
				if err == nil {
					t.Fatalf("SeedHistory(%q, %q) = nil, want a validation error",
						tt.target, tt.from)
				}
				if errors.Is(err, ErrNoHistory) {
					t.Errorf("error = %v, want a validation error rather than ErrNoHistory", err)
				}

				if _, err := os.Stat(outside); !errors.Is(err, os.ErrNotExist) {
					t.Errorf("something was written outside baseDir at %q (stat err = %v)",
						outside, err)
				}
				got, err := os.ReadFile(HistoryFile(base, "dst"))
				if err != nil {
					t.Fatalf("reading the target history: %v", err)
				}
				if string(got) != "{\"stale\":true}\n" {
					t.Errorf("target history = %q, want it untouched by a rejected call", got)
				}
			})
		}
	})
}
