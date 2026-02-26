package filesystem

import (
	"fmt"
	"os"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func init() { types.Register("createfile", CreatefileJob) }

func CreatefileJob(job types.Job) (types.Execution, error) {
	path := job.Parameters["path"].(string)

	file, err := os.Create(path)
	if err != nil {
		return types.Execution{
			Msg:    err.Error(),
			Failed: true,
		}, err
	}

	filename := file.Name()

	file.Close()

	return types.Execution{
		Output: fmt.Sprintf("Created file: %v", filename),
		Msg:    "ok\n",
		Failed: false,
	}, nil
}

