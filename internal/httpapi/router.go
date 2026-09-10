package httpapi

import (
	"net/http"
)

// Base paths for the route groups registered in Routes.
const (
	projectsEndpoint = "/projects"
	healthEndpoint   = "/health"
	configEndpoint   = "/config"
	versionEndpoint  = "/version"
)

// Routes builds the HTTP handler for the whole service: it registers every
// route (see the HTTP API section of README.md for request/response examples)
// and wraps the mux with the recoverer, requestID and logger middleware, in
// that outer-to-inner order.
func (s *Server) Routes() http.Handler {
	r := http.NewServeMux()

	r.HandleFunc("GET "+healthEndpoint, s.healthCheck)
	r.HandleFunc("GET "+projectsEndpoint, s.listProjects)
	r.HandleFunc("GET "+configEndpoint, s.getConfig)
	r.HandleFunc("GET "+versionEndpoint, s.getVersion)
	r.HandleFunc("GET "+projectsEndpoint+"/{id}", s.getProject)
	r.HandleFunc("GET "+projectsEndpoint+"/{id}/reports/{path...}", s.serveProjectReport)
	r.HandleFunc("GET "+projectsEndpoint+"/{id}/generation", s.generationStatus)
	r.HandleFunc("GET "+projectsEndpoint+"/{id}/report/export", s.exportReport)
	r.HandleFunc("GET "+projectsEndpoint+"/{id}/latest-report", s.latestReport)

	r.HandleFunc("POST "+projectsEndpoint, s.createProject)
	r.HandleFunc("POST "+projectsEndpoint+"/{id}/results", s.sendResults)
	r.HandleFunc("POST "+projectsEndpoint+"/{id}/generation", s.startGeneration)
	r.HandleFunc("POST "+projectsEndpoint+"/{id}/history/clean", s.clearHistory)
	r.HandleFunc("POST "+projectsEndpoint+"/{id}/history/seed", s.seedHistory)

	r.HandleFunc("DELETE "+projectsEndpoint+"/{id}", s.deleteProject)
	r.HandleFunc("DELETE "+projectsEndpoint+"/{id}/results", s.clearResults)
	return recoverer(requestID(logger(r)))
}

// healthCheck reports service liveness. GET /health, no params, always 200.
func (s *Server) healthCheck(w http.ResponseWriter, _ *http.Request) {
	_, err := w.Write([]byte("service is ok\n"))
	if err != nil {
		return
	}

}
