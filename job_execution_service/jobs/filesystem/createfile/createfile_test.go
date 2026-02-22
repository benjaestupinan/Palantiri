package filesystem

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func TestCreatefileJob_HappyPath(t *testing.T) {
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "test_file.txt")

	job := types.Job{
		Parameters: map[string]any{"path": path},
	}

	exec, err := CreatefileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Msg != "ok\n" {
		t.Fatalf("unexpected message: %q", exec.Msg)
	}

	if _, statErr := os.Stat(path); os.IsNotExist(statErr) {
		t.Fatalf("file was not created at path: %s", path)
	}
}

func TestCreatefileJob_InvalidPath(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{"path": "/nonexistent/directory/file.txt"},
	}

	exec, err := CreatefileJob(job)
	if err == nil {
		t.Fatalf("expected error but got nil")
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed")
	}
}

func TestCreatefileJob_FileAlreadyExists(t *testing.T) {
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "existing_file.txt")

	existing, err := os.Create(path)
	if err != nil {
		t.Fatalf("failed to create initial file: %v", err)
	}
	existing.WriteString("original content")
	existing.Close()

	job := types.Job{
		Parameters: map[string]any{"path": path},
	}

	exec, err := CreatefileJob(job)
	if err != nil {
		t.Fatalf("unexpected error when file already exists: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed when file already exists")
	}
}
