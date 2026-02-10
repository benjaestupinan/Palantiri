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
		fmt.Println("--- Routing ---")
		fmt.Println("Job doesnt exist in the router")
		fmt.Println("---------------")
		return
	}

	exec, err := fn(job)

	if err != nil {
		fmt.Println("--- Error fuera de flujo ---")
		fmt.Println(err)
		http.Error(w, "internal error", http.StatusInternalServerError)
		fmt.Println("----------------------------")
	}

	if exec.Failed {
		// error while execution job
		fmt.Println("--- Execution ---")
		fmt.Printf("Failed: %t\n", exec.Failed)
		fmt.Printf("Error: %s\n", exec.Msg)
		http.Error(w, exec.Msg, http.StatusBadRequest)
		fmt.Println("-----------------")

		return
	}

	fmt.Println("+++ Execution +++")
	fmt.Printf("Failed: %t\n", exec.Failed)
	fmt.Printf("Message: %s\n", exec.Msg)
	fmt.Printf("Output: %s\n", exec.Output)
	fmt.Println("+++++++++++++++++")
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
