package jobs

import (
	"bytes"
	"os/exec"
)


func EchoJob(job Job) ( Execution, error ) {
	cmd := exec.Command("echo", job.Parameters["message"].(string)) // prepare de command

	var output bytes.Buffer // define a variable to store the output


	cmd.Stdout = &output // set command output to the buffer

	err := cmd.Run() // You know what this does

	if err != nil {
		return Execution{
			Output: output.String(),
			Msg: err.Error(),
			Failed: true,
		}, err
	}

	return Execution{
		Output: output.String(),
		Msg: "ok\n",
		Failed: false,
	}, nil
}
