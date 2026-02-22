package editfile

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/benjaestupinan/job-execution-service/jobs/types"
)

// writeTestFile es un helper que crea un archivo temporal con el contenido dado.
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
			"path":  path,
			"edits": []Edit{{linenum: 2, newline: "edited line 2"}},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}
	if exec.Msg != "ok\n" {
		t.Fatalf("unexpected message: %q", exec.Msg)
	}
	if exec.Output != "File edited correctly" {
		t.Fatalf("unexpected output: %q", exec.Output)
	}

	// Verificar que el archivo fue realmente modificado en disco.
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file after edit: %v", err)
	}
	lines := strings.Split(string(data), "\n")
	if lines[1] != "edited line 2" {
		t.Fatalf("expected line 2 to be %q, got %q", "edited line 2", lines[1])
	}
}

func TestEditfileJob_FileNotFound(t *testing.T) {
	job := types.Job{
		Parameters: map[string]any{
			"path":  "/nonexistent/directory/file.txt",
			"edits": []Edit{{linenum: 1, newline: "new line"}},
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

	tmp.WriteString(strings.Repeat("a", 102401))
	tmp.Close()

	job := types.Job{
		Parameters: map[string]any{
			"path":  tmp.Name(),
			"edits": []Edit{{linenum: 1, newline: "new line"}},
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
			"edits": []Edit{
				{linenum: 1, newline: "edited line 1"},
				{linenum: 3, newline: "edited line 3"},
			},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed")
	}

	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file after edits: %v", err)
	}
	lines := strings.Split(string(data), "\n")
	if lines[0] != "edited line 1" {
		t.Fatalf("expected line 1 to be %q, got %q", "edited line 1", lines[0])
	}
	if lines[2] != "edited line 3" {
		t.Fatalf("expected line 3 to be %q, got %q", "edited line 3", lines[2])
	}
}

func TestEditfileJob_NoEdits(t *testing.T) {
	content := "line 1\nline 2\nline 3"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path":  path,
			"edits": []Edit{},
		},
	}

	exec, err := EditfileJob(job)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if exec.Failed {
		t.Fatalf("execution should not have failed with empty edits")
	}

	// El archivo no debe haber cambiado.
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed to read file: %v", err)
	}
	if string(data) != content {
		t.Fatalf("file content should not have changed")
	}
}

func TestEditfileJob_LineOutOfBounds(t *testing.T) {
	content := "line 1\nline 2"
	path := writeTestFile(t, content)

	job := types.Job{
		Parameters: map[string]any{
			"path":  path,
			"edits": []Edit{{linenum: 99, newline: "out of bounds"}},
		},
	}

	// Actualmente la función hace panic en este caso.
	// Este test documenta el comportamiento esperado: retornar error, no panic.
	defer func() {
		if r := recover(); r != nil {
			t.Fatalf("function panicked on out-of-bounds linenum: %v", r)
		}
	}()

	exec, err := EditfileJob(job)
	if err == nil && !exec.Failed {
		t.Fatalf("expected failure for out-of-bounds linenum")
	}
}
