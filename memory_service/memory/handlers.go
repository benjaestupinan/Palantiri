package memory

import (
	"encoding/json"
	"net/http"
	"strconv"
)

func HandleCreateSession(w http.ResponseWriter, r *http.Request) {
	id, err := CreateSession()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"session_id": id})
}

type messageRequest struct {
	SessionID string `json:"session_id"`
	Role      string `json:"role"`
	Content   string `json:"content"`
}

func HandleSaveMessage(w http.ResponseWriter, r *http.Request) {
	var req messageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}

	if req.SessionID == "" || req.Role == "" || req.Content == "" {
		http.Error(w, "session_id, role and content are required", http.StatusBadRequest)
		return
	}

	if err := SaveMessage(req.SessionID, req.Role, req.Content); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
}

func HandleGetMessages(w http.ResponseWriter, r *http.Request) {
	sessionID := r.PathValue("sessionID")
	n := 10
	if nStr := r.URL.Query().Get("n"); nStr != "" {
		if parsed, err := strconv.Atoi(nStr); err == nil {
			n = parsed
		}
	}

	messages, err := GetMessages(sessionID, n)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if messages == nil {
		messages = []Message{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(messages)
}

func HandleSearch(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query().Get("q")
	if q == "" {
		http.Error(w, "q parameter is required", http.StatusBadRequest)
		return
	}

	limit := 10
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if parsed, err := strconv.Atoi(limitStr); err == nil {
			limit = parsed
		}
	}

	results, err := Search(q, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if results == nil {
		results = []SearchResult{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}
