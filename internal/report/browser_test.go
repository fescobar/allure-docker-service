package report

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// This file opens a finished report in a real browser, which is the only check
// that catches "the page is dead" as a class rather than one known symptom.
// The defect that took production down had nothing to do with anything the
// other tests assert: every url was written where it belonged, the CLI built a
// report, the service served it in under 80ms - and clicking a test threw in
// the browser and unmounted the whole UI. The console said so; nothing else
// did.
//
// Chrome is driven through --dump-dom rather than a browser-automation
// library. It loads the page, lets its JavaScript run, and prints the DOM it
// ended up with, which is enough to tell a rendered report from an unmounted
// one - and it costs no dependency, no npm install and no downloaded browser.
// --enable-logging=stderr adds the console output on top, so the page's own
// errors come back as text.

// chromeCandidates are the paths a headless Chrome is looked for under, bare
// names included: exec.LookPath searches PATH for those.
var chromeCandidates = []string{
	"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
	"/Applications/Chromium.app/Contents/MacOS/Chromium",
	"google-chrome",
	"google-chrome-stable",
	"chromium",
	"chromium-browser",
}

// requireChrome returns a path to Chrome or skips the test. A machine without
// a browser cannot answer the question this file asks, and failing there would
// only teach people to ignore the failure.
func requireChrome(t *testing.T) string {
	t.Helper()

	for _, candidate := range chromeCandidates {
		if path, err := exec.LookPath(candidate); err == nil {
			return path
		}
	}
	t.Skip("no Chrome or Chromium found, cannot open the report in a browser")
	return ""
}

// anOpenedTest returns the id of one test in the report and the name that test
// carries. The id is the name of its file under data/test-results, and it is
// also what goes in the page's fragment: opening a test is a client-side
// route, so "#<id>" is the browser equivalent of clicking it in the tree.
func anOpenedTest(t *testing.T, reportDir string) (id, name string) {
	t.Helper()

	entries, err := os.ReadDir(filepath.Join(reportDir, "data", "test-results"))
	if err != nil {
		t.Fatalf("reading the report's test results: %v", err)
	}

	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".json") {
			continue
		}
		raw, err := os.ReadFile(filepath.Join(reportDir, "data", "test-results", e.Name()))
		if err != nil {
			t.Fatalf("reading %s: %v", e.Name(), err)
		}
		var result struct {
			Name string `json:"name"`
		}
		if err := json.Unmarshal(raw, &result); err != nil {
			t.Fatalf("test result %s is not valid JSON: %v", e.Name(), err)
		}
		if result.Name == "" {
			continue
		}
		return strings.TrimSuffix(e.Name(), ".json"), result.Name
	}

	t.Fatal("the built report has no test results to open")
	return "", ""
}

// TestReportOpensATestInABrowser is the end of the chain the other tests only
// cover in pieces: a report built by the real CLI, served over HTTP, opened at
// a test the way a click opens it, in a browser that runs its JavaScript.
//
// It asserts two things, and both are needed. The step of the opened test has
// to appear in the DOM, which says the test's own page rendered rather than
// unmounted; and the console has to be silent, which is what actually spoke up
// when the page died. A page can also fail by rendering an error boundary with
// no console output at all, which is why the DOM is checked and not only the
// log.
func TestReportOpensATestInABrowser(t *testing.T) {
	chrome := requireChrome(t)

	dir, projectID := generateTwice(t)
	reportDir := filepath.Join(dir, projectID, "reports", "latest")

	id, name := anOpenedTest(t, reportDir)

	// The report has to be served over HTTP: it fetches its own data, and a
	// browser refuses those requests from a file:// page.
	srv := httptest.NewServer(http.FileServer(http.Dir(reportDir)))
	defer srv.Close()

	ctx, cancel := context.WithTimeout(t.Context(), 90*time.Second)
	defer cancel()

	cmd := exec.CommandContext(ctx, chrome,
		"--headless",
		"--disable-gpu",
		// Required wherever the test runs as root, which is the normal
		// case in a container; harmless elsewhere.
		"--no-sandbox",
		// A fresh profile per run: Chrome refuses to share one, and a
		// stale profile is a source of failures that have nothing to do
		// with the report.
		"--user-data-dir="+t.TempDir(),
		// Fast-forwards timers instead of waiting on them, so the page
		// gets its full startup without the test sleeping through it.
		"--virtual-time-budget=15000",
		"--enable-logging=stderr",
		"--log-level=0",
		"--dump-dom",
		srv.URL+"/#"+id,
	)

	var stderr strings.Builder
	cmd.Stderr = &stderr
	dom, err := cmd.Output()
	if err != nil {
		t.Fatalf("chrome failed to open the report: %v\n%s", err, stderr.String())
	}

	if !strings.Contains(string(dom), testStepName) {
		t.Errorf("the page opened at test %q does not show that test's step; the report either unmounted or never rendered the test\nconsole:\n%s",
			name, consoleLines(stderr.String()))
	}

	for _, line := range consoleErrors(stderr.String()) {
		t.Errorf("the report logged an error while opening a test: %s", line)
	}
}

// consoleLines returns the page's console output, dropping Chrome's own
// chatter about GPUs and sandboxes.
func consoleLines(stderr string) string {
	var kept []string
	for _, line := range strings.Split(stderr, "\n") {
		if strings.Contains(line, ":CONSOLE:") {
			kept = append(kept, strings.TrimSpace(line))
		}
	}
	if len(kept) == 0 {
		return "(empty)"
	}
	return strings.Join(kept, "\n")
}

// consoleErrors returns the console lines that report a throw. Warnings and
// logs are left alone deliberately: a report is free to be noisy, and a test
// that fails on any output at all would be turned off the first time Allure
// added a deprecation notice. An uncaught exception is different - that is the
// shape the defect took, and there is no healthy reason for one.
func consoleErrors(stderr string) []string {
	var errs []string
	for _, line := range strings.Split(stderr, "\n") {
		if !strings.Contains(line, ":CONSOLE:") {
			continue
		}
		if strings.Contains(line, "Uncaught") {
			errs = append(errs, strings.TrimSpace(line))
		}
	}
	return errs
}
