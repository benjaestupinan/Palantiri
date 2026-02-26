package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/benjaestupinan/job-execution-service/jobs"

	// Registrar nuevo job: agregar un blank import aquí
	_ "github.com/benjaestupinan/job-execution-service/jobs/echo"
	_ "github.com/benjaestupinan/job-execution-service/jobs/filesystem/createfile"
	_ "github.com/benjaestupinan/job-execution-service/jobs/filesystem/editfile"
	_ "github.com/benjaestupinan/job-execution-service/jobs/filesystem/list_working_directory"
	_ "github.com/benjaestupinan/job-execution-service/jobs/filesystem/readfile"
	_ "github.com/benjaestupinan/job-execution-service/jobs/get_system_date_and_time"
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
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("--- Routing ---\n"))
		w.Write([]byte("Job doesnt exist in the router\n"))
		w.Write([]byte("---------------\n"))
		return
	}

	exec, err := fn(job)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
    w.Write([]byte("--- Error fuera de flujo ---\n"))
    w.Write([]byte(err.Error()))
    w.Write([]byte("\n----------------------------\n"))
    return
	}

	if exec.Failed {
		// error while execution job
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("--- Execution ---\n"))
		w.Write(fmt.Appendf(nil, "Failed: %t\n", exec.Failed))
		w.Write(fmt.Appendf(nil, "Error: %s\n", exec.Msg))
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
