package filesystem

import (
	"os"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)


func ListWorkingDirectoryJob(job types.Job) (types.Execution, error) {

	path := job.Parameters["path"].(string)

	entries, err := os.ReadDir(path)

	if err != nil {
		return types.Execution{
			Output: "Error",
			Msg: err.Error(),
			Failed: true,
		}, err
	}

	full_dir_string := ""

	for _, entry := range entries {
		full_dir_string += entry.Name()
		full_dir_string += " "
	}

	return types.Execution{
		Output: full_dir_string,
		Msg: 		"ok\n",
		Failed: false,
	}, nil
}
