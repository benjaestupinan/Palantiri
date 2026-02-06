# DoBot
My try at creating Jarvis
```txt
┌──────────────────────────────┐
│           Usuario            │
└───────────────┬──────────────┘
                │ lenguaje natural
                ▼
┌──────────────────────────────┐
│   1. Intent Router (LLM)     │
│  Clasifica tipo de intención │
└───────────────┬──────────────┘
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌─────────────────────┐
│ 2A. Chat /   │  │ 2B. System Action   │
│ Reasoning    │  │     Selector (LLM)  │
│ (LLM libre)  │  │  Selección de jobs  │
└──────────────┘  └───────────┬─────────┘
                               │ Job AST
                               ▼
                    ┌─────────────────────┐
                    │ 3. Job Validator    │
                    │  Schema + Policies  │
                    └───────────┬─────────┘
                               │ Job validado
                               ▼
                    ┌─────────────────────┐
                    │ 4. Job Normalizer   │
                    │  (determinista)     │
                    └───────────┬─────────┘
                               │ Job normalizado
                               ▼
                    ┌─────────────────────┐
                    │ 5. Job Executor     │
                    │  (sin IA)           │
                    └───────────┬─────────┘
                               │ resultado
                               ▼
                    ┌─────────────────────┐
                    │ 6. Result Formatter │
                    └─────────────────────┘
```
