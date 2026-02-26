package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var (
	paramRegex  = regexp.MustCompile(`job\.Parameters\["(\w+)"\]\.\(([^\)]+)\)`)
	structRegex = regexp.MustCompile(`type\s+(\w+)\s+struct\s*\{([^}]+)\}`)
	fieldRegex  = regexp.MustCompile(`(\w+)\s+(\w+)`)
)

func goTypeToJSONType(goType string) string {
	switch {
	case strings.HasPrefix(goType, "[]"):
		return "array"
	case goType == "string":
		return "string"
	case goType == "bool":
		return "boolean"
	case strings.Contains(goType, "int") || strings.Contains(goType, "float"):
		return "number"
	default:
		return "object"
	}
}

// parseStructs returns a map of struct name -> (field name -> field type)
func parseStructs(content []byte) map[string]map[string]string {
	structs := make(map[string]map[string]string)
	for _, m := range structRegex.FindAllSubmatch(content, -1) {
		fields := make(map[string]string)
		for _, fm := range fieldRegex.FindAllStringSubmatch(string(m[2]), -1) {
			fields[fm[1]] = fm[2]
		}
		structs[string(m[1])] = fields
	}
	return structs
}

// buildParamSchema builds the JSON schema for a parameter given its Go type.
// If the type is a slice of a known struct, it expands the struct fields as items.properties.
func buildParamSchema(goType string, structs map[string]map[string]string) map[string]interface{} {
	schema := make(map[string]interface{})
	if strings.HasPrefix(goType, "[]") {
		schema["type"] = "array"
		elemType := goType[2:]
		if fields, ok := structs[elemType]; ok {
			props := make(map[string]interface{})
			for name, typ := range fields {
				props[name] = map[string]interface{}{"type": goTypeToJSONType(typ)}
			}
			schema["items"] = map[string]interface{}{
				"type":       "object",
				"properties": props,
			}
		}
	} else {
		schema["type"] = goTypeToJSONType(goType)
	}
	return schema
}

func main() {
	jobsDir := "./jobs"
	outputFile := "../JOB_CATALOG.json"

	// Load existing catalog to preserve manually written descriptions
	catalog := make(map[string]map[string]interface{})
	existingData, err := os.ReadFile(outputFile)
	if err == nil {
		if err := json.Unmarshal(existingData, &catalog); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: could not parse existing catalog: %v\n", err)
		}
	}

	err = filepath.Walk(jobsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			return nil
		}
		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}
		if info.Name() == "router.go" || strings.Contains(filepath.ToSlash(path), "/types/") {
			return nil
		}

		jobID := filepath.Base(filepath.Dir(path))

		content, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("reading %s: %w", path, err)
		}

		structs := parseStructs(content)
		matches := paramRegex.FindAllSubmatch(content, -1)

		job, exists := catalog[jobID]
		if !exists {
			job = make(map[string]interface{})
		}
		job["job_id"] = jobID

		existingParams, _ := job["parameters"].(map[string]interface{})
		if existingParams == nil {
			existingParams = make(map[string]interface{})
		}

		for _, match := range matches {
			paramName := string(match[1])
			goType := strings.TrimSpace(string(match[2]))
			schema := buildParamSchema(goType, structs)

			// Preserve existing description if present
			if existing, ok := existingParams[paramName].(map[string]interface{}); ok {
				if desc, ok := existing["description"]; ok {
					schema["description"] = desc
				}
			}
			existingParams[paramName] = schema
		}

		job["parameters"] = existingParams
		catalog[jobID] = job

		fmt.Printf("  job: %-35s params: %d\n", jobID, len(existingParams))
		return nil
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error walking jobs directory: %v\n", err)
		os.Exit(1)
	}

	jsonBytes, err := json.MarshalIndent(catalog, "", "    ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		os.Exit(1)
	}

	if err := os.WriteFile(outputFile, append(jsonBytes, '\n'), 0644); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing catalog: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\nGenerated %s with %d jobs\n", outputFile, len(catalog))
}
