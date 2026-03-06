package get_recent_context

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func init() { types.Register("get_recent_context", GetRecentContextJob) }

func GetRecentContextJob(job types.Job) (types.Execution, error) {
	host := os.Getenv("MEMORY_HOST")
	port := os.Getenv("MEMORY_PORT")
	if port == "" {
		port = "8082"
	}

	endpoint := fmt.Sprintf("http://%s:%s/recent_messages?exclude_session=&n=20", host, port)
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
		return types.Execution{Output: "No hay conversaciones anteriores registradas.", Msg: "ok"}, nil
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
