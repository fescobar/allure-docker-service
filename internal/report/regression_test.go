package report

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/y-krenta/allure3-docker-service-go/internal/projects"
)

// The regression gate in CI does not compute anything itself: it reads the
// "transition" field Allure writes for every test in widgets/tree.json and
// blocks a merge request on "regressed" or "malfunctioned". That field is
// another program's output, and nothing else in this repository looks at it -
// so if a future Allure renames it, stops writing it into tree.json, or
// changes what it compares against, every test here stays green while the gate
// quietly stops blocking anything. A gate that fails open is worse than none,
// because the pipeline still reports success.
//
// Hence a test on the whole arrangement rather than on any one piece: a
// baseline project builds green, a second project is seeded from it, and the
// second build flips one test to failed. Nothing is stubbed - only the real
// CLI can say what the real CLI writes.

// writeResultWithStatus drops one result file into a project's results dir,
// under a caller-chosen history id and status. The history id is what ties a
// test in one build to the same test in another: Allure compares by it, not by
// name, and a seeded history is a file full of them.
func writeResultWithStatus(t *testing.T, baseDir, projectID, historyID, status string, n int) {
	t.Helper()

	uuid := fmt.Sprintf("00000000-0000-4000-8000-%012d", n)
	body := fmt.Sprintf(`{
		"uuid": %q,
		"historyId": %q,
		"fullName": "suite.%s",
		"name": %q,
		"status": %q,
		"stage": "finished",
		"start": 1700000000000,
		"stop": 1700000000250
	}`, uuid, historyID, historyID, historyID, status)

	path := filepath.Join(projects.ResultsDir(baseDir, projectID), uuid+"-result.json")
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatalf("writing result file: %v", err)
	}
}

// treeLeaf is the part of a widgets/tree.json leaf the gate reads.
type treeLeaf struct {
	NodeID     string `json:"nodeId"`
	Name       string `json:"name"`
	Status     string `json:"status"`
	Transition string `json:"transition"`
}

// readTreeLeaves returns the leaves of a published report keyed by test name.
func readTreeLeaves(t *testing.T, baseDir, projectID string) map[string]treeLeaf {
	t.Helper()

	path := filepath.Join(projects.LatestReportDir(baseDir, projectID), "widgets", "tree.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("reading tree.json: %v", err)
	}

	var tree struct {
		LeavesByID map[string]treeLeaf `json:"leavesById"`
	}
	if err := json.Unmarshal(raw, &tree); err != nil {
		t.Fatalf("decoding tree.json: %v", err)
	}

	byName := make(map[string]treeLeaf, len(tree.LeavesByID))
	for _, leaf := range tree.LeavesByID {
		byName[leaf.Name] = leaf
	}
	return byName
}

func TestSeededHistoryMakesAFailureRegressed(t *testing.T) {
	allure := requireAllureCLI(t)

	dir := t.TempDir()
	const baseline, mr = "baseline", "mr-1"
	for _, id := range []string{baseline, mr} {
		if err := projects.CreateDir(dir, id); err != nil {
			t.Fatalf("CreateDir(%q) = %v", id, err)
		}
	}
	g := New(dir, allure, testHistoryLimit, testBaseURL)

	writeResultWithStatus(t, dir, baseline, "steady", "passed", 1)
	writeResultWithStatus(t, dir, baseline, "breaks", "passed", 2)
	if err := g.Generate(t.Context(), baseline); err != nil {
		t.Fatalf("Generate(baseline) = %v, want nil", err)
	}

	if err := projects.SeedHistory(dir, mr, baseline); err != nil {
		t.Fatalf("SeedHistory = %v, want nil", err)
	}

	writeResultWithStatus(t, dir, mr, "steady", "passed", 3)
	writeResultWithStatus(t, dir, mr, "breaks", "failed", 4)
	if err := g.Generate(t.Context(), mr); err != nil {
		t.Fatalf("Generate(mr) = %v, want nil", err)
	}

	leaves := readTreeLeaves(t, dir, mr)

	broken, ok := leaves["breaks"]
	if !ok {
		t.Fatalf("tree.json has no leaf named %q, only %v", "breaks", leaves)
	}
	if broken.Transition != "regressed" {
		t.Errorf("transition of the failing test = %q, want %q", broken.Transition, "regressed")
	}
	// The gate turns this into a link, so an empty one would point at the
	// report's front page and name a test it never opens.
	if broken.NodeID == "" {
		t.Error("the regressed leaf carries no nodeId, so the gate cannot link to it")
	}

	// Without this half the assertion above would also pass on a build where
	// every test came out regressed, which is what an unseeded project looks
	// like when the whole suite is red.
	steady, ok := leaves["steady"]
	if !ok {
		t.Fatalf("tree.json has no leaf named %q, only %v", "steady", leaves)
	}
	if steady.Transition != "" {
		t.Errorf("transition of the unchanged test = %q, want none", steady.Transition)
	}
}

// A project that keeps its own history compares each build against the one
// before it, so a test failing in both is a change in neither - and the gate,
// reading transitions, lets the second push through. Re-seeding before every
// build is what closes that, and it only holds if the seed overwrites.
func TestReseedingKeepsASecondFailureRegressed(t *testing.T) {
	allure := requireAllureCLI(t)

	dir := t.TempDir()
	const baseline, mr = "baseline", "mr-1"
	for _, id := range []string{baseline, mr} {
		if err := projects.CreateDir(dir, id); err != nil {
			t.Fatalf("CreateDir(%q) = %v", id, err)
		}
	}
	g := New(dir, allure, testHistoryLimit, testBaseURL)

	writeResultWithStatus(t, dir, baseline, "breaks", "passed", 1)
	if err := g.Generate(t.Context(), baseline); err != nil {
		t.Fatalf("Generate(baseline) = %v, want nil", err)
	}

	// Two pushes to the same merge request, each seeded and each red.
	for push := 1; push <= 2; push++ {
		if err := projects.ClearResults(dir, mr); err != nil {
			t.Fatalf("push %d: ClearResults = %v, want nil", push, err)
		}
		if err := projects.SeedHistory(dir, mr, baseline); err != nil {
			t.Fatalf("push %d: SeedHistory = %v, want nil", push, err)
		}
		writeResultWithStatus(t, dir, mr, "breaks", "failed", push)
		if err := g.Generate(t.Context(), mr); err != nil {
			t.Fatalf("push %d: Generate = %v, want nil", push, err)
		}
	}

	leaf, ok := readTreeLeaves(t, dir, mr)["breaks"]
	if !ok {
		t.Fatal("tree.json has no leaf named \"breaks\"")
	}
	if leaf.Transition != "regressed" {
		t.Errorf("transition on the second push = %q, want %q", leaf.Transition, "regressed")
	}
}
