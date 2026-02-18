package types

type Execution struct {
	Output string
	Msg    string
	Failed bool
}

type Job struct {
	JobID      string
	Parameters map[string]any
}

type JobFunc func(Job) (Execution, error)
