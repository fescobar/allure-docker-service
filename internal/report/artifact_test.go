package report

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"testing"

	"github.com/y-krenta/allure3-docker-service-go/internal/projects"
)

// The tests in this file build a report with the real Allure CLI and then look
// at what came out, which is the one thing the rest of the suite never does.
// Every other test stops at the config or the executor file - at what this
// service hands the CLI - and a value can be written there correctly and still
// reach the browser wrong, or not reach it at all. That gap is exactly where
// the relative-reportUrl defect lived: the config test was green, guarding the
// very string that killed the page.
//
// Two builds, not one. A report with no history behind it never asks the
// browser to construct a URL, so a single build is blind to the whole class of
// defect by construction - which is why a stand of a hundred tests looked
// healthy while production died.
//
// Where a url was found matters as much as its value. The project's
// history.jsonl carries one at the top of every line, and a check satisfied by
// that alone would pass on a single build and on a walk that never descends -
// both verified by mutation, both silently blind to the file the dying page
// actually reads. So the assertions below insist on urls from
// data/test-results, which is where a test's history panel gets them.

// requireAllureCLI returns the path to the real Allure CLI or skips the test.
// These tests are about what the CLI produces, so there is nothing to stand in
// for it: a fake CLI would only prove that the fake writes what it was told to.
func requireAllureCLI(t *testing.T) string {
	t.Helper()

	path, err := exec.LookPath("allure")
	if err != nil {
		t.Skip("allure CLI is not installed, cannot build a real report")
	}
	return path
}

// testStepName is written into every fixture result and asserted on by the
// browser test. It has to be a step rather than the test's own name: the name
// is printed in the tree on the left as well, so finding it proves only that
// the report rendered something, while a step is shown by the test's page and
// nowhere else.
const testStepName = "the step only an opened test shows"

// writeRealResult drops one result file the real CLI will accept into the
// project's results dir. The minimal shape the rest of the suite uses is
// enough for a fake CLI but not for Allure, which needs a uuid, a status and a
// window of time before it will treat the file as a test at all.
func writeRealResult(t *testing.T, baseDir, projectID string, n int) {
	t.Helper()

	uuid := fmt.Sprintf("00000000-0000-4000-8000-%012d", n)
	body := fmt.Sprintf(`{
		"uuid": %q,
		"historyId": "case-%d",
		"fullName": "suite.Test%d",
		"name": "Test %d",
		"status": "passed",
		"stage": "finished",
		"start": 1700000000000,
		"stop": 1700000000250,
		"steps": [
			{
				"name": %q,
				"status": "passed",
				"stage": "finished",
				"start": 1700000000000,
				"stop": 1700000000100
			}
		]
	}`, uuid, n, n, n, testStepName)

	path := filepath.Join(projects.ResultsDir(baseDir, projectID), uuid+"-result.json")
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatalf("writing result file: %v", err)
	}
}

// foundURL is one url together with the file it came from, because the
// assertions care about both.
type foundURL struct {
	file string // path relative to the projects dir
	url  string
}

// generateTwice builds a project's report twice with the real CLI and returns
// the projects dir and the project's id. Callers get a report that has history
// behind it, which is the only kind that exercises the urls at all.
func generateTwice(t *testing.T) (dir, projectID string) {
	t.Helper()

	allure := requireAllureCLI(t)

	dir = t.TempDir()
	projectID = "demo"
	if err := projects.CreateDir(dir, projectID); err != nil {
		t.Fatalf("CreateDir(%q) = %v", projectID, err)
	}
	for n := 1; n <= 3; n++ {
		writeRealResult(t, dir, projectID, n)
	}

	g := New(dir, allure, testHistoryLimit, testBaseURL)
	for build := 1; build <= 2; build++ {
		if err := g.Generate(t.Context(), projectID); err != nil {
			t.Fatalf("Generate (build %d) = %v, want nil", build, err)
		}
	}
	return dir, projectID
}

// buildReportWithHistory generates the project twice with the real CLI and
// returns every url the finished report and the project's history carry.
//
// The second build is the point: the first one has nothing to look back on, so
// its report holds no history entries and no trend, and none of the urls this
// is about exist yet.
func buildReportWithHistory(t *testing.T) []foundURL {
	t.Helper()

	dir, projectID := generateTwice(t)

	var found []foundURL
	collect := func(path string) {
		rel, err := filepath.Rel(dir, path)
		if err != nil {
			rel = path
		}
		for _, u := range urlsInJSONFile(t, path) {
			found = append(found, foundURL{file: filepath.ToSlash(rel), url: u})
		}
	}

	latest := projects.LatestReportDir(dir, projectID)
	err := filepath.WalkDir(latest, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && strings.HasSuffix(path, ".json") {
			collect(path)
		}
		return nil
	})
	if err != nil {
		t.Fatalf("walking the built report: %v", err)
	}
	collect(projects.HistoryFile(dir, projectID))

	return found
}

// requireTestResultURLs fails unless the report's own test-result files carry
// urls, and returns them together with everything else that was found.
//
// Without this the suite is one mutation away from proving nothing: a single
// build, or a walk that reads only the top level of each document, still finds
// the url at the head of every history.jsonl line and sails through every
// assertion below.
func requireTestResultURLs(t *testing.T, found []foundURL) []string {
	t.Helper()

	urls := make([]string, 0, len(found))
	seen := map[string]bool{}
	inTestResults := 0
	for _, f := range found {
		if strings.Contains(f.file, "/data/test-results/") {
			inTestResults++
		}
		if !seen[f.url] {
			seen[f.url] = true
			urls = append(urls, f.url)
		}
	}

	if inTestResults == 0 {
		t.Fatalf("no urls under data/test-results in the built report; found %d elsewhere, "+
			"which is not the file a test's history panel reads", len(found))
	}
	sort.Strings(urls)
	return urls
}

// urlsInJSONFile returns every value stored under a "url" key in path, at any
// depth. Depth is not a detail to skip: in history.jsonl the urls sit inside
// each testResult rather than at the top level, so a walk that only reads the
// outermost object sees a clean file and reports nothing.
//
// The file is decoded into any rather than a struct on purpose. A struct would
// describe the shape this service expects, and the shape is the CLI's to
// choose; the point here is to find urls wherever the CLI decided to put them.
func urlsInJSONFile(t *testing.T, path string) []string {
	t.Helper()

	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		t.Fatalf("reading %s: %v", path, err)
	}

	var found []string
	var walk func(any)
	walk = func(node any) {
		switch v := node.(type) {
		case map[string]any:
			for key, value := range v {
				if s, ok := value.(string); ok && key == "url" {
					found = append(found, s)
					continue
				}
				walk(value)
			}
		case []any:
			for _, item := range v {
				walk(item)
			}
		}
	}

	// history.jsonl holds one object per line; the report's own files are
	// each a single document.
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		var doc any
		if err := json.Unmarshal([]byte(line), &doc); err != nil {
			// Not every .json file in a report is a document this cares
			// about, and a file this cannot read is not a failure of the
			// property under test.
			return found
		}
		walk(doc)
	}
	return found
}

// TestGeneratedReportCarriesOnlyAbsoluteURLs is the end-to-end form of the
// defect that took production down: not "did we write the right string into
// the config" but "is every url in the finished report one a browser can
// resolve".
//
// It catches what the unit tests cannot. Those call reportURLFor,
// writeAllureConfig and writeExecutor directly, handing each a valid base as
// an argument, so a Generator that accepts a base and then loses it - a field
// never assigned, a value never threaded through - leaves every one of them
// green. Here the base only ever enters through New.
func TestGeneratedReportCarriesOnlyAbsoluteURLs(t *testing.T) {
	urls := requireTestResultURLs(t, buildReportWithHistory(t))

	for _, u := range urls {
		if !strings.HasPrefix(u, testBaseURL+"/") {
			t.Errorf("report url %q, want one built from the configured base %q", u, testBaseURL)
		}
	}
}

// TestGeneratedReportURLsSurviveNewURL asks the engine that does the
// rejecting. Go's url.Parse accepts "../4/index.html" without an error, so no
// assertion written in Go can tell a healthy url from the one that unmounted
// the report; new URL() is what the report's frontend actually calls, and what
// throws.
func TestGeneratedReportURLsSurviveNewURL(t *testing.T) {
	node, err := exec.LookPath("node")
	if err != nil {
		t.Skip("node is not installed, cannot exercise new URL()")
	}

	urls := requireTestResultURLs(t, buildReportWithHistory(t))

	var body strings.Builder
	for _, u := range urls {
		body.WriteString("new URL(" + strconv.Quote(u) + ");\n")
	}
	body.WriteString("console.log(\"ok\");\n")

	harness := filepath.Join(t.TempDir(), "harness.mjs")
	if err := os.WriteFile(harness, []byte(body.String()), 0o644); err != nil {
		t.Fatalf("writing harness: %v", err)
	}

	out, err := exec.CommandContext(t.Context(), node, harness).CombinedOutput()
	if err != nil {
		t.Fatalf("new URL() rejected a url the report carries, which is what kills the page:\n%s\nurls:\n%s",
			out, strings.Join(urls, "\n"))
	}
	if got := strings.TrimSpace(string(out)); got != "ok" {
		t.Errorf("harness said %q, want ok", got)
	}
}
