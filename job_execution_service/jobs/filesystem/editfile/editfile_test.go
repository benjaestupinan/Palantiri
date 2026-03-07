package editfile

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

func writeTestFile(t *testing.T, content string) string {
	t.Helper()
	tmpDir := t.TempDir()
	path := filepath.Join(tmpDir, "test_file.txt")
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}
	return path
}

func TestEditfileJob_HappyPath(t *testing.T) {
	content := "line 1\nline 2\nline 3"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path": path,
			"edits": []any{
				map[string]any{"old_string": "line 2", "new_string": "edited line 2"},
			},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed: %s", exec.Msg)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file after edit: %v", err)
	}
	expected := "line 1\nedited line 2\nline 3"
	if string(data) != expected {
		t.Fatalf("expected %q, got %q", expected, string(data))
	}
}

func TestEditfileJob_FileNotFound(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{
			"path": "/nonexistent/directory/file.txt",
			"edits": []any{
				map[string]any{"old_string": "x", "new_string": "y"},
			},
		},
	}

	exec, err := EditfileJob(job)
	if err == nil {
		t.Fatalf("expected error but got nil")
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed")
	}
}

func TestEditfileJob_FileTooLarge(t *testing.T) {
	tmp, err := os.CreateTemp("", "editfile_test_large_*.txt")
	if err != nil {
		t.Fatalf("failed to create temp file: %v", err)
	}
	defer os.Remove(tmp.Name())

	tmp.WriteString("start\n")
	for i := 0; i < 102400; i++ {
		tmp.WriteString("a")
	}
	tmp.Close()

	job := types.Job{
		Parameters: map[string]any{
			"path": tmp.Name(),
			"edits": []any{
				map[string]any{"old_string": "start", "new_string": "end"},
			},
		},
	}

	exec, err := EditfileJob(job)
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

func TestEditfileJob_MultipleEdits(t *testing.T) {
	content := "line 1\nline 2\nline 3\nline 4"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path": path,
			"edits": []any{
				map[string]any{"old_string": "line 1", "new_string": "edited line 1"},
				map[string]any{"old_string": "line 3", "new_string": "edited line 3"},
			},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed: %s", exec.Msg)
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file after edits: %v", err)
	}
	expected := "edited line 1\nline 2\nedited line 3\nline 4"
	if string(data) != expected {
		t.Fatalf("expected %q, got %q", expected, string(data))
	}
}

func TestEditfileJob_NoEdits(t *testing.T) {
	content := "line 1\nline 2\nline 3"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path":  path,
			"edits": []any{},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed with empty edits")
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file: %v", err)
	}
	if string(data) != content {
		t.Fatalf("file content should not have changed")
	}
}

func TestEditfileJob_OldStringNotFound(t *testing.T) {
	content := "line 1\nline 2\nline 3"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path": path,
			"edits": []any{
				map[string]any{"old_string": "this does not exist", "new_string": "replacement"},
			},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !exec.Failed {
		t.Fatalf("execution should have failed when old_string not found")
	}
}
