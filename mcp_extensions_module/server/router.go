package server

import "net/http"

func NewRouter() *http.ServeMux {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("MCP Extensions Module up and running\n"))
	})

	mux.HandleFunc("/catalog", handleCatalog)
	mux.HandleFunc("/execute", handleExecute)

	return mux
}
