package projects

import (
	"errors"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
)

var (
	// projectIDPattern is the allowed shape for a project ID: starts and
	// ends with a lowercase letter or digit, letters/digits/space/_/-
	// allowed in between.
	projectIDPattern = regexp.MustCompile(`^[a-z\d]([a-z\d _-]*[a-z\d])?$`)
	// resultFileNamePattern is the allowed shape for an uploaded result file
	// name: ASCII letters, digits, dot, underscore and hyphen. Covers every
	// name Allure generates (<uuid>-result.json, environment.properties, ...).
	resultFileNamePattern = regexp.MustCompile(`^[a-zA-Z0-9._-]+$`)
	// ErrProjectExists is returned by CreateDir when the project directory
	// already exists.
	ErrProjectExists = errors.New("project already exists")

	// ErrNoHistory is returned by SeedHistory when the source project has no
	// history to copy. It does not mean the call failed: the target's history
	// is cleared either way, so what SeedHistory promises still holds. What it
	// tells the caller is that a build seeded from this source would have
	// nothing to compare itself against - every test would come out as new,
	// and a check built on that comparison would pass by finding nothing
	// rather than by finding nothing wrong. Whether that is fatal is the
	// caller's decision, not this package's.
	ErrNoHistory = errors.New("source project has no history")
)

const (
	// DefaultProjectID is the reserved, always-present project. It is
	// bootstrapped on startup and cannot be deleted (see the httpapi
	// deleteProject handler).
	DefaultProjectID = "default"
	// ExecutorFileName is the fixed name of the executor metadata file the
	// service writes into ResultsDir before a build. The watcher must skip
	// it when fingerprinting results, or writing it would look like new
	// results and trigger another build.
	ExecutorFileName = "executor.json"
)

// ResultsDir returns the path where a project's raw Allure results live:
// <baseDir>/<projectID>/results.
func ResultsDir(baseDir, projectID string) string {
	return filepath.Join(baseDir, projectID, "results")

}

// ReportsDir returns the path where a project's generated report builds
// live: <baseDir>/<projectID>/reports.
func ReportsDir(baseDir, projectID string) string {
	return filepath.Join(baseDir, projectID, "reports")

}

// LatestReportDir returns the path to a project's "latest" report build,
// a subdirectory of ReportsDir.
func LatestReportDir(baseDir, projectID string) string {
	return filepath.Join(ReportsDir(baseDir, projectID), "latest")
}

// ProjectDir returns the root of a single project's data: <baseDir>/<projectID>.
func ProjectDir(baseDir, projectID string) string {
	return filepath.Join(baseDir, projectID)
}

// TmpRoot returns the path where a project's in-progress report builds are
// staged: <baseDir>/<projectID>/.tmp. It deliberately sits beside ReportsDir
// rather than inside it, so half-built reports are invisible to anything
// listing the project's builds. Staging here also keeps the finished build on
// the same filesystem as LatestReportDir, which is what lets it be published
// with a rename.
func TmpRoot(baseDir, projectID string) string {
	return filepath.Join(baseDir, projectID, ".tmp")
}

// ValidateProjectID checks id against projectIDPattern and a 200-character
// length limit, returning a descriptive error if either check fails.
func ValidateProjectID(id string) error {
	if id == "" {
		return errors.New("project ID is required")
	}
	if len(id) > 200 {
		return errors.New("project ID must not exceed 200 characters")
	}
	if !projectIDPattern.MatchString(id) {
		return errors.New(`project ID may contain only lowercase letters, digits, spaces, underscores (_), and hyphens (-), and must start and end with a letter or digit`)
	}

	return nil
}

// CreateDir creates a new project's directory tree (the project dir plus
// its ReportsDir and ResultsDir subdirectories) under baseDir. Returns
// ErrProjectExists if the project directory is already there. If any step
// after the initial directory creation fails, it rolls back by removing
// everything it created.
func CreateDir(baseDir, id string) error {
	err := os.Mkdir(filepath.Join(baseDir, id), 0755)

	if errors.Is(err, fs.ErrExist) {
		return ErrProjectExists
	}

	if err != nil {
		return fmt.Errorf("unable to create project directory: %w", err)
	}

	ok := false
	defer func() {
		if !ok {
			if rmErr := os.RemoveAll(filepath.Join(baseDir, id)); rmErr != nil {
				log.Printf("rollback failed: %v\n", rmErr)
			}
		}
	}()

	err = os.MkdirAll(ReportsDir(baseDir, id), 0755)
	if err != nil {
		return fmt.Errorf("unable to create reports directory: %w", err)
	}

	err = os.MkdirAll(ResultsDir(baseDir, id), 0755)
	if err != nil {
		return fmt.Errorf("unable to create results directory: %w", err)
	}

	ok = true

	return nil
}

// ClearResults removes the top-level files in a project's results
// directory, leaving any subdirectories in place. It mirrors the
// "-maxdepth 1 -type f" behaviour of the original cleanAllureResults.sh:
// a directory sitting in results/ is left for whatever put it there.
//
// A missing results directory is returned as-is (wrapping fs.ErrNotExist)
// rather than translated to a sentinel here - that is the caller's job,
// the same as with a plain os.ReadDir elsewhere in this package.
func ClearResults(baseDir, projectID string) error {
	resultsDir := ResultsDir(baseDir, projectID)

	entries, err := os.ReadDir(resultsDir)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		err := os.Remove(filepath.Join(resultsDir, entry.Name()))
		if err != nil {
			return err
		}
	}
	return nil
}

// SanitizeResultFileName reduces a client-supplied file name to a single
// path element safe to create inside a project's results directory.
//
// Any directory part is stripped silently, so "a/b/x.json" becomes "x.json".
// The remaining name is rejected if it is a directory reference ("." or ".."),
// longer than 255 bytes, or contains anything outside ASCII letters, digits,
// ".", "_" and "-".
//
// The returned error describes the reason and is safe to show to the client.
func SanitizeResultFileName(name string) (string, error) {
	name = filepath.Base(name)
	switch name {
	case "", ".", "..", string(filepath.Separator):
		return "", fmt.Errorf("unsafe file name %q", name)

	}

	if len(name) > 255 {
		return "", fmt.Errorf("file name too long: %d bytes", len(name))
	}
	if !resultFileNamePattern.MatchString(name) {
		return "", fmt.Errorf("invalid character in file name: %q", name)
	}

	return name, nil
}

// HistoryFile returns the path to a project's Allure history:
// <baseDir>/<projectID>/history.jsonl, one JSON object per past run. The
// Allure CLI keeps it up to date itself, given the path.
//
// It sits in the project root rather than in ResultsDir on purpose. The
// watcher rebuilds a project when the listing of its results directory
// changes, and every build appends to this file - inside ResultsDir it would
// make each build trigger the next one, forever.
func HistoryFile(baseDir, projectID string) string {
	return filepath.Join(baseDir, projectID, "history.jsonl")
}

// NumberedReportDir returns the path to a project's archived report build
// numbered n, a subdirectory of ReportsDir alongside LatestReportDir. n comes
// from the build's own count of past reports, not from any input a caller
// controls.
func NumberedReportDir(baseDir, projectID string, n int) string {
	path := filepath.Join(ReportsDir(baseDir, projectID), fmt.Sprintf("%d", n))
	return path
}

// SeedHistory replaces projectID's trend history with fromProjectID's, so that
// the next build of projectID is measured against the source project's past
// runs instead of its own. The file is copied byte for byte; nothing in it is
// rewritten or merged.
//
// It is meant to be called before every build of the target, not once when the
// target is created. A target that keeps the history of its own previous build
// compares each run against the run before it - and a test that fails in two
// consecutive runs is then a change in neither of them, which is exactly the
// comparison seeding exists to avoid.
//
// What the call promises is that projectID's history ends up identical to
// fromProjectID's, the empty case included: a source with no history leaves the
// target with none and returns ErrNoHistory. That is not a failed copy, and the
// removal happens first for that reason - returning early would leave the
// target holding a history the source does not have.
//
// The new history is staged beside its destination and renamed over it, the
// same way Generate publishes a report. A reader - a build staging the history
// for the Allure CLI - then sees either the whole old file or the whole new
// one, never a half-written one, which the CLI rejects outright. The staging
// file lives in the project's own directory rather than in TmpRoot because
// rename does not cross filesystems.
//
// Both IDs are validated here rather than taken on trust: this package owns the
// on-disk layout, so it cannot leave that check to whoever happens to call it
// today. A target project that does not exist is reported as-is (wrapping
// fs.ErrNotExist), the same convention ClearResults follows, and is checked up
// front rather than left to surface from the copy - without that check the
// empty-source path would answer ErrNoHistory for a project that is not there
// at all.
func SeedHistory(baseDir, projectID, fromProjectID string) error {
	if err := ValidateProjectID(fromProjectID); err != nil {
		return fmt.Errorf("invalid source project ID: %w", err)
	}
	if err := ValidateProjectID(projectID); err != nil {
		return fmt.Errorf("invalid project ID: %w", err)
	}
	if projectID == fromProjectID {
		return fmt.Errorf("project ID (%s) and source project ID (%s) must be different", projectID, fromProjectID)
	}

	if _, err := os.Stat(ProjectDir(baseDir, projectID)); err != nil {
		return err
	}

	pathHistorySrc := HistoryFile(baseDir, fromProjectID)
	pathHistoryDst := HistoryFile(baseDir, projectID)
	tmp := pathHistoryDst + ".seed"
	data, err := os.ReadFile(pathHistorySrc)
	if errors.Is(err, fs.ErrNotExist) {
		err = os.Remove(pathHistoryDst)
		if err != nil && !errors.Is(err, fs.ErrNotExist) {
			return fmt.Errorf("removing history: %w", err)
		}
		return ErrNoHistory
	}
	if err != nil {
		return fmt.Errorf("reading history file: %w", err)
	}

	err = os.WriteFile(tmp, data, 0o644)
	defer func() { _ = os.Remove(tmp) }()
	if err != nil {
		return fmt.Errorf("write history: %w", err)
	}

	if err := os.Rename(tmp, pathHistoryDst); err != nil {
		return fmt.Errorf("rename history file: %w", err)
	}
	return nil
}

// ClearHistory resets everything that gives a project's report its trend
// history: every numbered archive under ReportsDir (identified by a name
// that parses as a number - "latest" and anything else is left alone),
// the HistoryFile, and the results directory's ExecutorFileName. Deleting
// the numbered archives also resets the next build's number back to 1,
// which is why ExecutorFileName has to go too: writeExecutor in the report
// package is a no-op for build 1, so a stale executor.json from a higher
// build number would otherwise survive untouched.
//
// A missing ReportsDir is returned as-is (wrapping fs.ErrNotExist), the
// same convention as ClearResults. A missing HistoryFile is not an error -
// a project with no build yet has none - so that removal alone tolerates
// fs.ErrNotExist rather than propagating it.
func ClearHistory(baseDir, projectID string) error {
	entries, err := os.ReadDir(ReportsDir(baseDir, projectID))
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		_, err := strconv.Atoi(entry.Name())
		if err != nil {
			continue
		}
		err = os.RemoveAll(filepath.Join(ReportsDir(baseDir, projectID), entry.Name()))
		if err != nil {
			return err
		}
	}

	err = os.Remove(HistoryFile(baseDir, projectID))
	if err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}

	err = os.RemoveAll(filepath.Join(ResultsDir(baseDir, projectID), ExecutorFileName))
	if err != nil {
		return err
	}

	return nil
}

// CleanTmp removes the .tmp staging directory of every project under baseDir.
// It is meant to be called once at startup, and only then: it takes no locks,
// which is safe exactly because nothing has begun building yet. Calling it
// after the watcher or the HTTP server is up would let it delete a build's
// staging directory out from under a running Allure process.
//
// Generate already clears .tmp at the start of every build, so this only
// matters for projects that are never rebuilt: a build killed by a restart
// leaves its half-finished report behind, and without this sweep that garbage
// stays on disk for the life of the volume.
//
// Entries that are not directories, and directories whose name is not a valid
// project ID, are skipped rather than reported - they were not created by this
// service and are none of its business. A project whose .tmp cannot be removed
// is logged and the sweep continues, since one project with broken permissions
// should not stop the others from being cleaned. The returned error is
// reserved for the one failure that stops everything, being unable to list
// baseDir at all; a project that has no .tmp is not a failure, because
// os.RemoveAll reports success for a path that does not exist.
func CleanTmp(baseDir string) error {
	entries, err := os.ReadDir(baseDir)
	if err != nil {
		return fmt.Errorf("unable to read projects directory %q: %w", baseDir, err)
	}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		if err := ValidateProjectID(entry.Name()); err != nil {
			continue
		}

		path := TmpRoot(baseDir, entry.Name())
		if err := os.RemoveAll(path); err != nil {
			log.Printf("unable to remove temporary directory %q: %v", path, err)
		}
	}

	return nil
}
