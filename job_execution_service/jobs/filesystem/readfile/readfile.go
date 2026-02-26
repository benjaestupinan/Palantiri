package filesystem

import (
	"os"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func init() { types.Register("readfile", ReadfileJob) }

func ReadfileJob(job types.Job) (types.Execution, error) {
	path := job.Parameters["path"].(string)

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

	return types.Execution{
		Output: string(data),
		Msg:    "ok\n",
		Failed: false,
	}, nil
}
