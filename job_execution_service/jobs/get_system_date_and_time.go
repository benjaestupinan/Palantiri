package jobs

import "time"

func GetSystemDateAndTimeJob(job Job) ( Execution, error ) {
	
	current_time := time.Now()
	formatted_time := current_time.Format("2006-01-02 15:04:05")
	// I dont know why but this specific Date and Time formats it correctly
	// if this isnt the correct time, it doesnt work anymore and I couldnt tell you why
	return Execution{
		Output: formatted_time,
		Msg: "ok\n",
	}, nil
}
