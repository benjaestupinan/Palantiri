package search_memory

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func init() { types.Register("search_memory", SearchMemoryJob) }

func SearchMemoryJob(job types.Job) (types.Execution, error) {
	query, ok := job.Parameters["query"].(string)
	if !ok || query == "" {
		return types.Execution{Failed: true, Msg: "query parameter is required"}, nil
	}

	host := os.Getenv("MEMORY_HOST")
	port := os.Getenv("MEMORY_PORT")
	if port == "" {
		port = "8082"
	}

	endpoint := fmt.Sprintf("http://%s:%s/search?q=%s&limit=10", host, port, url.QueryEscape(query))
	resp, err := http.Get(endpoint)
	if err != nil {
		return types.Execution{Failed: true, Msg: fmt.Sprintf("error calling memory service: %s", err)}, nil
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return types.Execution{Failed: true, Msg: fmt.Sprintf("error reading response: %s", err)}, nil
	}

	var results []map[string]any
	if err := json.Unmarshal(body, &results); err != nil {
		return types.Execution{Failed: true, Msg: fmt.Sprintf("error parsing response: %s", err)}, nil
	}

	if len(results) == 0 {
		return types.Execution{Output: "No se encontraron resultados para esa búsqueda.", Msg: "ok"}, nil
	}

	output := ""
	for _, r := range results {
		date := fmt.Sprintf("%v", r["created_at"])[:10]
		role := "Usuario"
		if r["role"] == "assistant" {
			role = "Asistente"
		}
		output += fmt.Sprintf("[%s] %s: %v\n", date, role, r["content"])
	}

	return types.Execution{Output: output, Msg: "ok"}, nil
}
