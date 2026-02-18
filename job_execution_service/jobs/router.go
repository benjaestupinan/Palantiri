package jobs

import (
	"fmt"

	"github.com/benjaestupinan/job-execution-service/jobs/echo"
	"github.com/benjaestupinan/job-execution-service/jobs/get_system_date_and_time"
	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

type Execution = types.Execution
type Job = types.Job
type JobFunc = types.JobFunc

var jobHandlers = map[string]JobFunc{
	"echo":                     echo.EchoJob,
	"get_system_date_and_time": get_system_date_and_time.GetSystemDateAndTimeJob,
}

func JobRouter(jobID string) (JobFunc, error) {
	fn, ok := jobHandlers[jobID]
	if !ok {
		return nil, fmt.Errorf("unknown job: %s", jobID)
	}
	return fn, nil
}
