package jobs


import (
	"fmt"
)

func JobRouter(jobID string) (JobFunc, error) {

	fn, ok := jobHandlers[jobID]
	if !ok {
		return nil, fmt.Errorf("unknown job: %s", jobID)
	}
	return fn, nil
}


