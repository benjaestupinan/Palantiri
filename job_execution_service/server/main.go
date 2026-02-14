package main

import (
	"encoding/json"
	"fmt"
	"github.com/benjaestupinan/job-execution-service/jobs"
	"log"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
	var job jobs.Job

	err := json.NewDecoder(r.Body).Decode(&job)
	if err != nil {
		http.Error(w, "invalid json", http.StatusBadRequest)
		return
	}

	job.JobID = r.PathValue("jobID")

	fn, err := jobs.JobRouter(job.JobID)
	if err != nil {
		// job doesnt exist in the router
		w.Write([]byte("--- Routing ---\n"))
		w.Write([]byte("Job doesnt exist in the router\n"))
		w.Write([]byte("---------------\n"))
		return
	}

	exec, err := fn(job)

	if err != nil {
		w.Write([]byte("--- Error fuera de flujo ---\n"))
		w.Write([]byte(err.Error()))
		http.Error(w, "internal error", http.StatusInternalServerError)
		w.Write([]byte("----------------------------\n"))
	}

	if exec.Failed {
		// error while execution job
		w.Write([]byte("--- Execution ---\n"))
		w.Write(fmt.Appendf(nil, "Failed: %t\n", exec.Failed))
		w.Write(fmt.Appendf(nil, "Error: %s\n", exec.Msg))
		http.Error(w, exec.Msg, http.StatusBadRequest)
		w.Write([]byte("-----------------\n"))

		return
	}

	w.Write([]byte("+++ Execution +++\n"))
	w.Write(fmt.Appendf(nil, "Failed: %t\n", exec.Failed))
	w.Write(fmt.Appendf(nil, "Message: %s\n", exec.Msg))
	w.Write(fmt.Appendf(nil, "Output: %s\n", exec.Output))
	w.Write([]byte("+++++++++++++++++\n"))
}

func main() {
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Server up and running\n"))
	})

	mux.HandleFunc("/job/{jobID}", handler)

	log.Println("Go service running on :8081")
	log.Fatal(http.ListenAndServe(":8081", mux))
}
