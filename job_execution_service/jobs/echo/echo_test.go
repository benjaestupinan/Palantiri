package echo

import (
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func TestEchoJob_NormalMessage(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{"message": "hello world"},
	}

	exec, err := EchoJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != "hello world\n" {
		t.Errorf("expected 'hello world\\n', got %q", exec.Output)
	}
}

func TestEchoJob_EmptyMessage(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{"message": ""},
	}

	exec, err := EchoJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != "\n" {
		t.Errorf("expected '\\n', got %q", exec.Output)
	}
}

func TestEchoJob_SpecialCharacters(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{"message": "hello!@#$%^&*()"},
	}

	exec, err := EchoJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != "hello!@#$%^&*()\n" {
		t.Errorf("expected 'hello!@#$%%^&*()\\n', got %q", exec.Output)
	}
}

func TestEchoJob_MissingParameter(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{},
	}

	defer func() {
		if r := recover(); r == nil {
			t.Errorf("expected panic for missing 'message' parameter")
		}
	}()

	EchoJob(job)
}
