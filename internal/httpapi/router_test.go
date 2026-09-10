package httpapi

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/y-krenta/allure3-docker-service-go/internal/report"
)

// TestRoutes drives the real mux, so a mistyped pattern or a wildcard in the
// wrong place shows up here instead of at service start.
func TestRoutes(t *testing.T) {
	s, _ := newTestServer(t, "demo")
	// The generation routes need a generator that answers. hasStatus makes the
	// status route reply 200, which a missing route could not fake: the mux
	// answers an unregistered path with 404 too.
	s.reports = &stubGenerator{hasStatus: true, status: report.Status{State: report.StateRunning}}
	h := s.Routes()

	body, ct := multipartBody(t, uploadFile{"files[]", "a-result.json", `{"uuid":"a"}`})

	tests := []struct {
		name        string
		method      string
		target      string
		body        *strings.Reader
		contentType string
		wantStatus  int
	}{
		{name: "health", method: http.MethodGet, target: "/health", wantStatus: http.StatusOK},
		{name: "list projects", method: http.MethodGet, target: "/projects", wantStatus: http.StatusOK},
		{name: "get project", method: http.MethodGet, target: "/projects/demo", wantStatus: http.StatusOK},
		{name: "create project", method: http.MethodPost, target: "/projects",
			body: strings.NewReader(`{"project_id":"fresh"}`), contentType: "application/json", wantStatus: http.StatusCreated},
		{name: "delete project", method: http.MethodDelete, target: "/projects/fresh", wantStatus: http.StatusNoContent},
		{name: "serve report", method: http.MethodGet, target: "/projects/demo/reports/latest/app.js", wantStatus: http.StatusNotFound},
		{name: "start generation", method: http.MethodPost, target: "/projects/demo/generation", wantStatus: http.StatusAccepted},
		{name: "generation status", method: http.MethodGet, target: "/projects/demo/generation", wantStatus: http.StatusOK},
		// The source has no history, so the handler answers 409 - a status the
		// mux cannot produce on its own, unlike the 404 an unregistered path
		// gets.
		{name: "seed history", method: http.MethodPost, target: "/projects/demo/history/seed",
			body: strings.NewReader(`{"from_project_id":"baseline"}`), contentType: "application/json", wantStatus: http.StatusConflict},

		{name: "unknown path", method: http.MethodGet, target: "/nope", wantStatus: http.StatusNotFound},
		{name: "wrong method on projects", method: http.MethodPut, target: "/projects", wantStatus: http.StatusMethodNotAllowed},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var r *http.Request
			if tt.body != nil {
				r = httptest.NewRequest(tt.method, tt.target, tt.body)
				r.Header.Set("Content-Type", tt.contentType)
			} else {
				r = httptest.NewRequest(tt.method, tt.target, nil)
			}

			w := httptest.NewRecorder()
			h.ServeHTTP(w, r)

			if w.Code != tt.wantStatus {
				t.Fatalf("%s %s = %d, want %d (body: %s)", tt.method, tt.target, w.Code, tt.wantStatus, w.Body)
			}
		})
	}

	t.Run("send results reaches the upload handler", func(t *testing.T) {
		r := httptest.NewRequest(http.MethodPost, "/projects/demo/results", body)
		r.Header.Set("Content-Type", ct)

		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)

		if w.Code != http.StatusOK {
			t.Fatalf("status = %d, want %d (body: %s)", w.Code, http.StatusOK, w.Body)
		}
		if !strings.Contains(w.Body.String(), "a-result.json") {
			t.Errorf("body = %s, want the uploaded file listed", w.Body)
		}
	})

	t.Run("every response carries a request id", func(t *testing.T) {
		r := httptest.NewRequest(http.MethodGet, "/health", nil)
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)

		if w.Header().Get("X-Request-ID") == "" {
			t.Error("X-Request-ID header is missing")
		}
	})
}

func TestRecoverer(t *testing.T) {
	t.Run("turns a panic into 500", func(t *testing.T) {
		h := recoverer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
			panic("boom")
		}))

		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/", nil))

		if w.Code != http.StatusInternalServerError {
			t.Fatalf("status = %d, want %d", w.Code, http.StatusInternalServerError)
		}
	})

	t.Run("leaves a healthy handler alone", func(t *testing.T) {
		h := recoverer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			w.WriteHeader(http.StatusTeapot)
		}))

		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/", nil))

		if w.Code != http.StatusTeapot {
			t.Fatalf("status = %d, want %d", w.Code, http.StatusTeapot)
		}
	})
}

func TestRequestID(t *testing.T) {
	var seen string

	h := requestID(http.HandlerFunc(func(_ http.ResponseWriter, r *http.Request) {
		seen, _ = r.Context().Value(requestIDKey).(string)
	}))

	w := httptest.NewRecorder()
	h.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/", nil))

	header := w.Header().Get("X-Request-ID")
	if header == "" {
		t.Fatal("X-Request-ID header is missing")
	}
	if seen != header {
		t.Errorf("context id = %q, header = %q, want them equal", seen, header)
	}
}

func TestStatusRecorder(t *testing.T) {
	w := httptest.NewRecorder()
	rec := &statusRecorder{ResponseWriter: w, status: http.StatusOK}

	rec.WriteHeader(http.StatusTeapot)

	if rec.status != http.StatusTeapot {
		t.Errorf("recorded status = %d, want %d", rec.status, http.StatusTeapot)
	}
	if w.Code != http.StatusTeapot {
		t.Errorf("delegated status = %d, want %d", w.Code, http.StatusTeapot)
	}
}

func TestUnwrapResponseWriter(t *testing.T) {
	inner := httptest.NewRecorder()
	wrapped := &statusRecorder{ResponseWriter: &statusRecorder{ResponseWriter: inner}}

	// http.MaxBytesReader reaches the writer that owns the connection with a
	// bare type assertion instead of an Unwrap walk, so a handler that wants an
	// oversized request answered with a clean 413 - and the connection closed
	// rather than drained - has to hand it the writer underneath the
	// middleware itself.
	if got := unwrapResponseWriter(wrapped); got != http.ResponseWriter(inner) {
		t.Errorf("unwrapResponseWriter returned %T, want the innermost *httptest.ResponseRecorder", got)
	}
	if got := unwrapResponseWriter(inner); got != http.ResponseWriter(inner) {
		t.Errorf("unwrapResponseWriter(%T) = %T, want it returned unchanged", inner, got)
	}
}
