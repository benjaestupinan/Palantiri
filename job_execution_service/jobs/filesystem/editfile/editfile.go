package editfile

import (
	"fmt"
	"os"
	"strings"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

type Edit struct {
	OldString string
	NewString string
}

func init() { types.Register("editfile", EditfileJob) }

func EditfileJob(job types.Job) (types.Execution, error) {
	path := job.Parameters["path"].(string)

	rawEdits, ok := job.Parameters["edits"].([]any)
	if !ok {
		return types.Execution{Msg: "edits must be an array", Failed: true}, nil
	}

	var edits []Edit
	for _, e := range rawEdits {
		m, ok := e.(map[string]any)
		if !ok {
			return types.Execution{Msg: "each edit must be an object", Failed: true}, nil
		}
		oldStr, ok1 := m["old_string"].(string)
		newStr, ok2 := m["new_string"].(string)
		if !ok1 || !ok2 {
			return types.Execution{Msg: "each edit must have old_string and new_string", Failed: true}, nil
		}
		edits = append(edits, Edit{OldString: oldStr, NewString: newStr})
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return types.Execution{Msg: err.Error(), Failed: true}, err
	}

	if len(data) > 102400 {
		return types.Execution{Msg: "file is larger than 100KB", Failed: true}, nil
	}

	content := string(data)

	for _, edit := range edits {
		if !strings.Contains(content, edit.OldString) {
			return types.Execution{
				Msg:    fmt.Sprintf("old_string not found in file: %q", edit.OldString),
				Failed: true,
			}, nil
		}
		content = strings.Replace(content, edit.OldString, edit.NewString, 1)
	}

	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		return types.Execution{Msg: err.Error(), Failed: true}, err
	}

	return types.Execution{Output: "File edited correctly", Msg: "ok\n"}, nil
}
