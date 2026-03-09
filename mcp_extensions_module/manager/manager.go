package manager

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"sync"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type serverConfig struct {
	Command  string            `json:"command"`
	Args     []string          `json:"args"`
	Env      map[string]string `json:"env,omitempty"`
	Category string            `json:"category,omitempty"`
}

type serversFile struct {
	MCPServers map[string]serverConfig `json:"mcpServers"`
}

// ParameterSpec mirrors the JOB_CATALOG parameter format expected by the Python client.
type ParameterSpec struct {
	Type        string `json:"type"`
	Description string `json:"description,omitempty"`
	Required    bool   `json:"required"`
}

// CatalogEntry mirrors the JOB_CATALOG entry format expected by the Python client.
type CatalogEntry struct {
	JobID       string                   `json:"job_id"`
	Category    string                   `json:"category,omitempty"`
	Description string                   `json:"description"`
	Parameters  map[string]ParameterSpec `json:"parameters"`
}

type registeredTool struct {
	serverName   string
	originalName string
	category     string
	session      *mcp.ClientSession
	description  string
	inputSchema  any
}

// Manager holds all active MCP server sessions and their registered tools.
type Manager struct {
	mu    sync.RWMutex
	tools map[string]*registeredTool // jobID → tool
}

var Global = &Manager{
	tools: make(map[string]*registeredTool),
}

// Init reads mcp_servers.json and connects to all configured MCP servers.
func (m *Manager) Init(configPath string) error {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return fmt.Errorf("reading config: %w", err)
	}

	var cfg serversFile
	if err := json.Unmarshal(data, &cfg); err != nil {
		return fmt.Errorf("parsing config: %w", err)
	}

	for name, srv := range cfg.MCPServers {
		if err := m.connectServer(name, srv); err != nil {
			fmt.Printf("[manager] failed to connect to server %q: %v\n", name, err)
		}
	}
	return nil
}

func (m *Manager) connectServer(name string, cfg serverConfig) error {
	cmd := exec.Command(cfg.Command, cfg.Args...)

	// Inherit parent environment so system tools (node, npx, etc.) are in PATH.
	if len(cfg.Env) > 0 {
		cmd.Env = os.Environ()
		for k, v := range cfg.Env {
			cmd.Env = append(cmd.Env, k+"="+v)
		}
	}

	client := mcp.NewClient(
		&mcp.Implementation{Name: "lens-mcp-client", Version: "v1.0.0"},
		nil,
	)

	transport := &mcp.CommandTransport{Command: cmd}
	session, err := client.Connect(context.Background(), transport, nil)
	if err != nil {
		return fmt.Errorf("connecting: %w", err)
	}

	result, err := session.ListTools(context.Background(), nil)
	if err != nil {
		session.Close()
		return fmt.Errorf("listing tools: %w", err)
	}

	m.mu.Lock()
	defer m.mu.Unlock()

	for _, tool := range result.Tools {
		jobID := name + "_" + tool.Name
		m.tools[jobID] = &registeredTool{
			serverName:   name,
			originalName: tool.Name,
			category:     cfg.Category,
			session:      session,
			description:  tool.Description,
			inputSchema:  tool.InputSchema,
		}
		fmt.Printf("[manager] registered tool %q from server %q\n", jobID, name)
	}
	return nil
}

// Catalog returns all registered MCP tools as JOB_CATALOG-compatible entries.
func (m *Manager) Catalog() map[string]CatalogEntry {
	m.mu.RLock()
	defer m.mu.RUnlock()

	catalog := make(map[string]CatalogEntry)
	for jobID, tool := range m.tools {
		catalog[jobID] = CatalogEntry{
			JobID:       jobID,
			Category:    tool.category,
			Description: tool.description,
			Parameters:  schemaToParams(tool.inputSchema),
		}
	}
	return catalog
}

// Execute calls an MCP tool and returns its text output.
func (m *Manager) Execute(jobID string, parameters map[string]any) (string, error) {
	m.mu.RLock()
	tool, ok := m.tools[jobID]
	m.mu.RUnlock()

	if !ok {
		return "", fmt.Errorf("unknown job_id: %s", jobID)
	}

	result, err := tool.session.CallTool(context.Background(), &mcp.CallToolParams{
		Name:      tool.originalName,
		Arguments: parameters,
	})
	if err != nil {
		return "", fmt.Errorf("calling tool: %w", err)
	}

	var output string
	for _, content := range result.Content {
		if tc, ok := content.(*mcp.TextContent); ok {
			output += tc.Text
		}
	}
	if result.IsError {
		return "", fmt.Errorf("tool %q error: %s", tool.originalName, output)
	}
	return output, nil
}

// schemaToParams converts a JSON Schema object's properties to ParameterSpec map.
// schema is an any value (typically map[string]any) deserialized from JSON.
func schemaToParams(schema any) map[string]ParameterSpec {
	params := make(map[string]ParameterSpec)
	if schema == nil {
		return params
	}
	m, ok := schema.(map[string]any)
	if !ok {
		return params
	}
	props, ok := m["properties"].(map[string]any)
	if !ok {
		return params
	}
	required := map[string]bool{}
	if reqList, ok := m["required"].([]any); ok {
		for _, r := range reqList {
			if s, ok := r.(string); ok {
				required[s] = true
			}
		}
	}
	for propName, propVal := range props {
		propMap, ok := propVal.(map[string]any)
		if !ok {
			continue
		}
		t, _ := propMap["type"].(string)
		if t == "" {
			t = "string"
		}
		desc, _ := propMap["description"].(string)
		params[propName] = ParameterSpec{
			Type:        t,
			Description: desc,
			Required:    required[propName],
		}
	}
	return params
}
