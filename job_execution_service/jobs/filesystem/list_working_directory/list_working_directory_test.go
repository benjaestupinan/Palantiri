package filesystem

import (
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)


func TestListWorkingDirectory_ThisDir(t *testing.T) {

	job := types.Job{
		Parameters: map[string]any{
			"path": ".",
		},
	}

	exec, err := ListWorkingDirectoryJob(job)

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != "list_working_directory.go list_working_directory_test.go " {
		t.Fatalf("\nexpected: list_working_directory.go list_working_directory_test.go\nrecieved: %v", exec.Output)
	}
}

func TestListWorkingDirectory_InvalidPath(t *testing.T) {

	job := types.Job{
		Parameters: map[string]any{
			"path": "/nonexistent/path",
		},
	}

	exec, err := ListWorkingDirectoryJob(job)

	if err == nil {
		t.Fatalf("expected error for invalid path, got nil")
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed for invalid path")
	}
}
