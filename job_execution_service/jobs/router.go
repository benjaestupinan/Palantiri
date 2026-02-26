package jobs

import (
	"fmt"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

type Execution = types.Execution
type Job = types.Job
type JobFunc = types.JobFunc

func JobRouter(jobID string) (JobFunc, error) {
	fn, ok := types.Registry[jobID]
	if !ok {
		return nil, fmt.Errorf("unknown job: %s", jobID)
	}
	return fn, nil
}
