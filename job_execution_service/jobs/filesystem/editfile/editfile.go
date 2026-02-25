package editfile

import (
	"os"
	"strings"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

type Edit struct {
	linenum int
newline string
}

func EditfileJob(job types.Job) (types.Execution, error) {
	path := job.Parameters["path"].(string)
	edits := job.Parameters["edits"].([]Edit)

	data, err := os.ReadFile(path)
	if err != nil {
		return types.Execution{
			Msg:    err.Error(),
			Failed: true,
		}, err
	}

	if len(data) > 102400 {
		return types.Execution{
			Msg:    "file is larger than 100KB",
			Failed: true,
		}, nil
	}

	file_lines := strings.Split(string(data), "\n")

	for _, edit := range edits {
		for edit.linenum > len(file_lines) {
			file_lines = append(file_lines, "")
		}
		file_lines[edit.linenum -1] = edit.newline
	}

	os.WriteFile(path, []byte(strings.Join(file_lines, "\n")), 0644)

	return types.Execution{
		Output: "File edited correctly",
		Msg: 		"ok\n",
		Failed: false,
	}, nil
}
