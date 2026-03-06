package main

import (
	"log"
	"net/http"

	"github.com/benjaestupinan/memory-service/memory"
)

func main() {
	if err := memory.Connect(); err != nil {
		log.Fatalf("Failed to connect to PostgreSQL: %v", err)
	}
	log.Println("Connected to PostgreSQL")

	mux := http.NewServeMux()

	mux.HandleFunc("POST /session", memory.HandleCreateSession)
	mux.HandleFunc("POST /message", memory.HandleSaveMessage)
	mux.HandleFunc("GET /session/{sessionID}/messages", memory.HandleGetMessages)
	mux.HandleFunc("GET /search", memory.HandleSearch)
	mux.HandleFunc("GET /recent_messages", memory.HandleGetRecentMessages)

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Memory service up and running\n"))
	})

	log.Println("Memory service running on :8082")
	log.Fatal(http.ListenAndServe(":8082", mux))
}
