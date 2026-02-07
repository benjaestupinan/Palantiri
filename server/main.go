package main

import (
	// "log"
	// "net/http"
	"fmt"
	"github.com/benjaestupinan/job-execution-service/jobs"
)

func main() {
	// mux := http.NewServeMux()
	//
	// mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
	// 	w.WriteHeader(http.StatusOK)
	// 	w.Write([]byte("ok"))
	// })
	//
	// log.Println("Go service running on :8081")
	// log.Fatal(http.ListenAndServe(":8081", mux))

	jobID := "echo"
	params := map[string]any{
		"message": "hola silvanita",
	}

	job := jobs.Job{
		JobID: jobID,
		Parameters: params,
	}

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
		// error while execution job
		fmt.Println("--- Execution ---")
		fmt.Printf("Failed: %t\n", exec.Failed)
		fmt.Printf("Error: %s\n", exec.Msg)
		fmt.Println("-----------------")

		return
	}

	fmt.Println("+++ Execution +++")
	fmt.Printf("Failed: %t\n", exec.Failed)
	fmt.Printf("Message: %s\n", exec.Msg)
	fmt.Printf("Output: %s\n", exec.Output)
	fmt.Println("+++++++++++++++++")

}
