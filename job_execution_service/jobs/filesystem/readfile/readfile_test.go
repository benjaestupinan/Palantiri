package filesystem

import (
	"os"
	"strings"
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func TestReadfileJob_HappyPath(t *testing.T) {
	tmp, err := os.CreateTemp("", "readfile_test_*.txt")
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}
	defer os.Remove(tmp.Name())

	content := "hello world"
	tmp.WriteString(content)
	tmp.Close()

	job := types.Job{
		Parameters: map[string]any{"path": tmp.Name()},
	}

	exec, err := ReadfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != content {
		t.Fatalf("\nexpected: %q\nreceived: %q", content, exec.Output)
	}
}

func TestReadfileJob_FileNotFound(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{"path": "/nonexistent/path/file.txt"},
	}

	exec, err := ReadfileJob(job)
	if err == nil {
		t.Fatalf("expected error but got nil")
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed")
	}
}

func TestReadfileJob_FileTooLarge(t *testing.T) {
	tmp, err := os.CreateTemp("", "readfile_test_large_*.txt")
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}
	defer os.Remove(tmp.Name())

	tmp.WriteString(strings.Repeat("a", 102401))
	tmp.Close()

	job := types.Job{
		Parameters: map[string]any{"path": tmp.Name()},
	}

	exec, err := ReadfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed for large file")
	}
	if exec.Msg != "file is larger than 100KB" {
		t.Fatalf("unexpected message: %q", exec.Msg)
	}
}

func TestReadfileJob_EmptyFile(t *testing.T) {
	tmp, err := os.CreateTemp("", "readfile_test_empty_*.txt")
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}
	defer os.Remove(tmp.Name())
	tmp.Close()

	job := types.Job{
		Parameters: map[string]any{"path": tmp.Name()},
	}

	exec, err := ReadfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Output != "" {
		t.Fatalf("expected empty output, got: %q", exec.Output)
	}
}
