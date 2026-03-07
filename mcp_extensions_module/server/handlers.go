package server

import (
	"encoding/json"
	"net/http"

	"github.com/benjaestupinan/mcp-extensions-module/manager"
)

func handleCatalog(w http.ResponseWriter, r *http.Request) {
	catalog := manager.Global.Catalog()
	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(catalog); err != nil {
		http.Error(w, "failed to encode catalog", http.StatusInternalServerError)
	}
}

type executeRequest struct {
	JobID      string         `json:"job_id"`
	Parameters map[string]any `json:"parameters"`
}

func handleExecute(w http.ResponseWriter, r *http.Request) {
	var req executeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}

	output, err := manager.Global.Execute(req.JobID, req.Parameters)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Write([]byte(output))
}
