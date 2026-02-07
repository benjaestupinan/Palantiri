package jobs

import (
)

type Execution struct {
	Output string
	Msg string
	Failed bool
}


type Job struct {
	JobID      string
	Parameters map[string]any
}

type JobFunc func(Job) (Execution, error)

var jobHandlers = map[string]JobFunc{
	"echo":        EchoJob,
	"get_system_time": GetSystemDateAndTimeJob,
}


