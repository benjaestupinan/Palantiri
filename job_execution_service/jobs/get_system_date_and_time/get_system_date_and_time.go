package get_system_date_and_time

import (
	"time"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func init() { types.Register("get_system_date_and_time", GetSystemDateAndTimeJob) }

func GetSystemDateAndTimeJob(job types.Job) (types.Execution, error) {
	current_time := time.Now()
	formatted_time := current_time.Format("2006-01-02 15:04:05")

	return types.Execution{
		Output: formatted_time,
		Msg:    "ok\n",
	}, nil
}
