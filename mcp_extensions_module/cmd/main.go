package main

import (
	"log"
	"net/http"
	"os"

	"github.com/benjaestupinan/mcp-extensions-module/manager"
	"github.com/benjaestupinan/mcp-extensions-module/server"
	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load("../.env"); err != nil {
		log.Println("No .env file found, reading from environment")
	}

	configPath := os.Getenv("MCP_SERVERS_CONFIG")
	if configPath == "" {
		configPath = "../mcp_servers.json"
	}

	if err := manager.Global.Init(configPath); err != nil {
		log.Printf("Warning: failed to initialize MCP manager: %v", err)
	}

	port := os.Getenv("MCP_EXTENSIONS_PORT")
	if port == "" {
		port = "8083"
	}

	mux := server.NewRouter()
	log.Printf("MCP Extensions Module running on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
