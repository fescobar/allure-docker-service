package httpapi

import (
	"encoding/json"
	"errors"
	"io/fs"
	"log/slog"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"slices"
	"strings"
	"time"

	"github.com/y-krenta/allure3-docker-service-go/internal/projects"
	"github.com/y-krenta/allure3-docker-service-go/internal/report"
)

// createProjectRequest is the JSON body expected by createProject.
type createProjectRequest struct {
	ProjectID string `json:"project_id"`
}

// listProjectsResponse is the JSON body returned by listProjects.
type listProjectsResponse struct {
	Projects []string `json:"projects"`
}

// projectBuildsResponse is the JSON body returned by getProject.
type projectBuildsResponse struct {
	Builds []string `json:"builds"`
}

// seedHistoryRequest is the JSON body expected by seedHistory: the project
// whose history is copied over the target's own.
type seedHistoryRequest struct {
	FromProjectID string `json:"from_project_id"`
}

// createProject handles POST /projects. Body: createProjectRequest. On
// success responds 201 with no body. Responds 400 for an invalid body or a
// project_id that fails projects.ValidateProjectID, 409 if the project
// already exists.
func (s *Server) createProject(w http.ResponseWriter, r *http.Request) {
	var req createProjectRequest

	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}

	errValidation := projects.ValidateProjectID(req.ProjectID)
	if errValidation != nil {
		http.Error(w, errValidation.Error(), http.StatusBadRequest)
		return
	}

	err = projects.CreateDir(s.projectsDir, req.ProjectID)
	switch {
	case errors.Is(err, projects.ErrProjectExists):
		http.Error(w, "project already exists", http.StatusConflict)
		return
	case err != nil:
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	default:
		w.WriteHeader(http.StatusCreated)
	}
}

// listProjects handles GET /projects. The optional "search" query param
// filters project IDs by a case-insensitive substring match. Responds 200
// with listProjectsResponse.
func (s *Server) listProjects(w http.ResponseWriter, r *http.Request) {
	search := strings.ToLower(r.URL.Query().Get("search"))
	entries, err := os.ReadDir(s.projectsDir)
	if err != nil {
		slog.Error("error read dir", "err", err)
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	}

	ids := make([]string, 0)
	for _, entry := range entries {
		if entry.IsDir() {
			name := strings.ToLower(entry.Name())
			if strings.Contains(name, search) {
				ids = append(ids, entry.Name())
			}
		}
	}

	resp := listProjectsResponse{Projects: ids}
	writeJSON(w, r, resp)
}

// deleteProject handles DELETE /projects/{id}. Removes the project
// directory recursively. Responds 204 on success, 400 if id fails
// projects.ValidateProjectID, 403 for the reserved default project
// (projects.DefaultProjectID).
func (s *Server) deleteProject(w http.ResponseWriter, r *http.Request) {
	id, ok := requireProjectID(w, r)
	if !ok {
		return
	}

	if id == projects.DefaultProjectID {
		slog.Error("It is forbidden to delete the default directory")
		http.Error(w, "The default directory cannot be deleted.", http.StatusForbidden)
		return
	}
	// Delete waits out a build in flight rather than pulling the directory out
	// from under it, so the reply has to outlive the server's WriteTimeout.
	liftWriteDeadline(w, lockWaitDeadline, id)

	err := s.reports.Delete(id)
	if err != nil {
		slog.Error("failed to delete project", "err", err, "project_id", id)
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

// getProject handles GET /projects/{id}. Lists the project's builds: report
// subdirectories that contain an index.html, sorted by that file's mtime
// descending, with "latest" always pinned first. Responds 200 with
// projectBuildsResponse, 400 if id fails projects.ValidateProjectID, 404 if
// the project directory doesn't exist.
func (s *Server) getProject(w http.ResponseWriter, r *http.Request) {
	// buildEntry pairs a build directory name with its index.html mtime,
	// used only to sort builds before the response is assembled.
	type buildEntry struct {
		Name string
		When time.Time
	}

	var items []buildEntry

	id, ok := requireProjectID(w, r)
	if !ok {
		return
	}
	projectPath := projects.ProjectDir(s.projectsDir, id)
	_, errStat := os.Stat(projectPath)
	if errors.Is(errStat, os.ErrNotExist) {
		http.Error(w, "project not found", http.StatusNotFound)
		return
	} else if errStat != nil {
		slog.Error("failed to stat project path", "err", errStat, "path", projectPath)
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	}
	builds := make([]string, 0)

	buildsPath := projects.ReportsDir(s.projectsDir, id)
	entries, err := os.ReadDir(buildsPath)
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		slog.Error("failed to read dir", "err", err, "path", buildsPath)
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		pathToIndex := filepath.Join(buildsPath, entry.Name(), "index.html")
		info, errStatIndex := os.Stat(pathToIndex)
		if errStatIndex != nil {
			if errors.Is(errStatIndex, os.ErrNotExist) {
				continue
			}
			slog.Error("failed to stat index file", "err", errStatIndex, "path", pathToIndex)
			http.Error(w, msgInternalError, http.StatusInternalServerError)
			return
		}
		items = append(items, buildEntry{Name: entry.Name(), When: info.ModTime()})

	}
	cmp := func(a, b buildEntry) int {
		return b.When.Compare(a.When)
	}
	slices.SortFunc(items, cmp)
	for _, item := range items {
		if item.Name == "latest" {
			builds = append([]string{item.Name}, builds...)
		} else {
			builds = append(builds, item.Name)
		}

	}

	resp := projectBuildsResponse{Builds: builds}
	writeJSON(w, r, resp)

}

// serveProjectReport handles GET /projects/{id}/reports/{path...}, serving the
// project's report tree as static files: the published "latest" build and every
// archived numbered one beside it.
//
// A directory is served only through an index.html of its own. Without that
// rule http.ServeFileFS answers with a generated listing of whatever the
// directory holds, and an Allure report is mostly directories that have none -
// data/, widgets/ and the rest, carrying attachment files, history and widget
// JSON. Nothing there is meant to be browsable, and the Flask service this
// replaced never listed a directory either.
//
// Nothing here is cacheable without revalidation. Every rebuild republishes the
// whole report at the same addresses, so a browser holding a cached copy has no
// way to notice it is looking at an old one. no-cache leaves the bytes in the
// cache but makes the browser ask before using them, and an unchanged file
// still answers 304 off the Last-Modified that ServeFileFS sets: the cost is a
// round trip, not a re-download. It also keeps the 301 below out of the
// permanent redirect cache, which is the same worry that has latestReport
// answering 302.
//
// Responds 200 with the file, 301 for an explicit index.html (net/http
// canonicalises it to "./"), 400 if id fails projects.ValidateProjectID or the
// path is empty, and 404 for anything absent - a directory without an
// index.html included.
func (s *Server) serveProjectReport(w http.ResponseWriter, r *http.Request) {
	id, ok := requireProjectID(w, r)
	if !ok {
		return
	}
	reportPath := r.PathValue("path")
	reportPath = path.Clean(reportPath)
	if reportPath == "." {
		http.Error(w, "path empty", http.StatusBadRequest)
		return
	}

	rootDir := os.DirFS(projects.ReportsDir(s.projectsDir, id))

	fi, err := fs.Stat(rootDir, reportPath)
	if err == nil && fi.IsDir() {
		if _, err := fs.Stat(rootDir, path.Join(reportPath, "index.html")); err != nil {
			http.NotFound(w, r)
			return
		}
	}

	// Set after the check above so a 404 does not carry it.
	w.Header().Set("Cache-Control", "no-cache")
	http.ServeFileFS(w, r, rootDir, reportPath)

}

// clearResults handles DELETE /projects/{id}/results. Removes the
// top-level files in the project's results directory; subdirectories are
// left alone. Responds 204 on success, including when results was already
// empty, 400 if id fails projects.ValidateProjectID, and 404 if the
// project has no results directory.
func (s *Server) clearResults(w http.ResponseWriter, r *http.Request) {
	id, ok := requireProjectID(w, r)
	if !ok {
		return
	}

	liftWriteDeadline(w, lockWaitDeadline, id)

	err := s.reports.ClearResults(id)
	if errors.Is(err, report.ErrProjectNotFound) {
		http.Error(w, "project not found", http.StatusNotFound)
		return
	}
	if err != nil {
		slog.Error("failed to clear results", "err", err)
		http.Error(w, msgInternalError, http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// seedHistory handles POST /projects/{id}/history/seed. Body:
// seedHistoryRequest. It replaces the project's history with a copy of
// another project's, which is what gives a merge-request project the
// baseline its regressions are measured against.
//
// The source ID arrives in the body rather than the path, so it gets its own
// projects.ValidateProjectID call here: both IDs reach filepath.Join, and the
// error the package returns for a bad one carries no sentinel to tell an
// invalid ID from a broken disk once it is back here.
//
// Responds 204 on success, 400 for an invalid body, either ID, or a source
// equal to the target, 404 if the target project does not exist, and 409 if
// the source has no history to
// copy - the request is well formed and the copy did happen, but a build
// seeded from an empty source has nothing to compare against, and a caller
// that treated that as success would be gating on a comparison that never
// took place.
func (s *Server) seedHistory(w http.ResponseWriter, r *http.Request) {
	var req seedHistoryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}
	id, ok := requireProjectID(w, r)
	if !ok {
		return
	}
	if err := projects.ValidateProjectID(req.FromProjectID); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	err := projects.SeedHistory(s.projectsDir, id, req.FromProjectID)
	switch {
	case errors.Is(err, projects.ErrNoHistory):
		http.Error(w, "source project has no history: run a build in it first", http.StatusConflict)
	case errors.Is(err, fs.ErrNotExist):
		http.Error(w, "project not found", http.StatusNotFound)
	case errors.Is(err, projects.ErrCopyToSelf):
		http.Error(w, "source and target project must differ", http.StatusBadRequest)

	case err != nil:
		slog.Error("failed to seed history", "err", err, "project_id", id)
		http.Error(w, msgInternalError, http.StatusInternalServerError)

	default:
		w.WriteHeader(http.StatusNoContent)
	}

}
