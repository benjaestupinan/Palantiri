package echo

import (
	"bytes"
	"os/exec"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func EchoJob(job types.Job) (types.Execution, error) {
	cmd := exec.Command("echo", job.Parameters["message"].(string))

	var output bytes.Buffer
	cmd.Stdout = &output

	err := cmd.Run()

	if err != nil {
		return types.Execution{
			Output: output.String(),
			Msg:    err.Error(),
			Failed: true,
		}, err
	}

	return types.Execution{
		Output: output.String(),
		Msg:    "ok\n",
		Failed: false,
	}, nil
}
