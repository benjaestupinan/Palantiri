package get_system_date_and_time

import (
	"testing"
	"time"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func TestGetSystemDateAndTimeJob_ReturnsValidDatetime(t *testing.T) {
	job := types.Job{}

	exec, err := GetSystemDateAndTimeJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output == "" {
		t.Fatal("output should not be empty")
	}
}

func TestGetSystemDateAndTimeJob_TimeInExpectedRange(t *testing.T) {
	before := time.Now()
	job := types.Job{}

	exec, err := GetSystemDateAndTimeJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	after := time.Now()

	parsed, err := time.ParseInLocation("2006-01-02 15:04:05", exec.Output, time.Local)
	if err != nil {
		t.Fatalf("failed to parse output time %q: %v", exec.Output, err)
	}

	if parsed.Before(before.Truncate(time.Second)) || parsed.After(after.Add(time.Second)) {
		t.Errorf("output time %v not in expected range [%v, %v]", parsed, before, after)
	}
}

func TestGetSystemDateAndTimeJob_CorrectFormat(t *testing.T) {
	job := types.Job{}

	exec, err := GetSystemDateAndTimeJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	_, err = time.Parse("2006-01-02 15:04:05", exec.Output)
	if err != nil {
		t.Errorf("output %q does not match expected format 'YYYY-MM-DD HH:MM:SS': %v", exec.Output, err)
	}
}
