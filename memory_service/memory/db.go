package memory

import (
	"context"
	"fmt"
	"os"

	"github.com/jackc/pgx/v5/pgxpool"
)

var pool *pgxpool.Pool

func Connect() error {
	connStr := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		os.Getenv("PGHOST"),
		os.Getenv("PGPORT"),
		os.Getenv("PGUSER"),
		os.Getenv("PGPASSWORD"),
		os.Getenv("PGDATABASE"),
	)

	var err error
	pool, err = pgxpool.New(context.Background(), connStr)
	return err
}

func CreateSession() (string, error) {
	var id string
	err := pool.QueryRow(context.Background(),
		"INSERT INTO sessions DEFAULT VALUES RETURNING id").Scan(&id)
	return id, err
}

func SaveMessage(sessionID, role, content string) error {
	_, err := pool.Exec(context.Background(),
		"INSERT INTO messages (session_id, role, content) VALUES ($1, $2, $3)",
		sessionID, role, content)
	return err
}

type Message struct {
	Role      string `json:"role"`
	Content   string `json:"content"`
	CreatedAt string `json:"created_at"`
}

func GetMessages(sessionID string, n int) ([]Message, error) {
	rows, err := pool.Query(context.Background(),
		`SELECT role, content, created_at::text FROM messages
		 WHERE session_id = $1
		 ORDER BY created_at DESC
		 LIMIT $2`,
		sessionID, n)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var messages []Message
	for rows.Next() {
		var m Message
		if err := rows.Scan(&m.Role, &m.Content, &m.CreatedAt); err != nil {
			return nil, err
		}
		messages = append(messages, m)
	}

	// Revertir a orden cronológico
	for i, j := 0, len(messages)-1; i < j; i, j = i+1, j-1 {
		messages[i], messages[j] = messages[j], messages[i]
	}

	return messages, nil
}

type SearchResult struct {
	SessionID string `json:"session_id"`
	Role      string `json:"role"`
	Content   string `json:"content"`
	CreatedAt string `json:"created_at"`
}

func Search(query string, limit int) ([]SearchResult, error) {
	rows, err := pool.Query(context.Background(),
		`SELECT m.session_id::text, m.role, m.content, m.created_at::text
		 FROM messages m
		 WHERE m.content ILIKE $1
		 ORDER BY m.created_at DESC
		 LIMIT $2`,
		"%"+query+"%", limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []SearchResult
	for rows.Next() {
		var r SearchResult
		if err := rows.Scan(&r.SessionID, &r.Role, &r.Content, &r.CreatedAt); err != nil {
			return nil, err
		}
		results = append(results, r)
	}

	return results, nil
}
