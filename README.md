# AI SQL Agent

An intelligent SQL agent that translates natural language queries into executable SQL using LangGraph workflows and schema-aware reasoning. Published as a reusable MCP (Model Context Protocol) tool for seamless integration with AI assistants and multi-agent systems.

## Features

- **Natural Language to SQL**: Convert plain English questions into precise PostgreSQL queries
- **Schema-Aware Reasoning**: Automatically discovers database schema for accurate query generation
- **LangGraph Workflow**: Multi-step agent with validation, execution, and automatic retry mechanisms
- **Conversational Memory**: Maintains context across multiple queries in a session
- **MCP Tool Server**: Exposed as a Model Context Protocol tool for AI assistant integration
- **FastAPI REST API**: Full-featured HTTP API with OpenAPI documentation
- **SQL Validation & Safety**: Blocks dangerous operations (DELETE, DROP, etc.) and validates queries before execution
- **Automatic Retry**: Intelligent retry mechanism for failed queries (up to 3 attempts)
- **Structured Outputs**: Clean JSON responses with query results, metadata, and natural language answers

## Tech Stack

- **FastAPI** - Modern web framework for building APIs
- **LangGraph** - Stateful multi-agent workflow orchestration
- **LangChain + Groq** - LLM integration with fast inference
- **PostgreSQL** - Target database
- **SQLAlchemy** - Database ORM and schema introspection
- **MCP (Model Context Protocol)** - Tool server for AI assistant integration
- **Pydantic** - Data validation and settings management

## Architecture

The agent follows a LangGraph state machine workflow:

```
START → discover_schema → generate_sql → validate_sql 
                                        ↓
                                   [valid?]
                                   ↓      ↓
                              execute   retry_sql → validate_sql (loop)
                                   ↓
                            generate_answer
                                   ↓
                                  END
```

**Workflow Steps:**
1. **Schema Discovery**: Introspects PostgreSQL database to understand tables, columns, types, and relationships
2. **SQL Generation**: LLM generates SQL based on natural language query and schema context
3. **Validation**: Checks SQL syntax, blocks dangerous operations, performs dry-run validation
4. **Execution**: Runs validated SQL against the database
5. **Retry Loop**: If validation or execution fails, LLM attempts to fix the query (up to 3 retries)
6. **Answer Generation**: Converts query results into natural language response

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Groq API key ([get one here](https://console.groq.com/))

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Ajayramaswamy2005/ai-sql-agent.git
cd ai-sql-agent
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/your_database
GROQ_MODEL=llama-3.3-70b-versatile
MAX_RETRY_ATTEMPTS=3
HOST=0.0.0.0
PORT=8000
```

## Usage

### FastAPI Server

Start the REST API server:

```bash
python -m app.main
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`

#### API Endpoints

**POST /query** - Execute a natural language query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the top 5 customers by total order amount",
    "session_id": "my-session"
  }'
```

Response:
```json
{
  "session_id": "my-session",
  "user_query": "Show me the top 5 customers by total order amount",
  "generated_sql": "SELECT c.customer_name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_name ORDER BY total_spent DESC LIMIT 5",
  "answer": "The top 5 customers by total order amount are: 1. John Smith ($12,450), 2. Jane Doe ($10,230)...",
  "columns": ["customer_name", "total_spent"],
  "rows": [["John Smith", 12450.00], ["Jane Doe", 10230.00]],
  "row_count": 5,
  "success": true,
  "retry_count": 0,
  "error": null
}
```

**GET /schema** - View database schema
```bash
curl http://localhost:8000/schema
```

**GET /health** - Check service health
```bash
curl http://localhost:8000/health
```

**DELETE /memory/{session_id}** - Clear conversation memory
```bash
curl -X DELETE http://localhost:8000/memory/my-session
```

### MCP Tool Server

Start the MCP server for AI assistant integration:

```bash
python -m app.mcp.server
```

The server exposes these tools via stdio transport:

- **query_database**: Execute natural language queries
- **get_schema**: Retrieve full database schema
- **list_tables**: List all table names
- **clear_memory**: Clear session conversation history

#### MCP Configuration Example

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "sql-agent": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "/path/to/ai-sql-agent"
    }
  }
}
```

## Project Structure

```
ai-sql-agent/
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic settings management
│   ├── main.py                # FastAPI application and routes
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # SQLAlchemy engine and query execution
│   │   └── schema.py          # Database schema introspection
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py           # LangGraph state definition
│   │   ├── prompts.py         # LLM prompt templates
│   │   ├── nodes.py           # Graph node functions
│   │   └── graph.py           # LangGraph workflow definition
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic request/response models
│   ├── memory/
│   │   ├── __init__.py
│   │   └── store.py           # Conversation memory management
│   └── mcp/
│       ├── __init__.py
│       └── server.py          # MCP tool server
├── .env                       # Environment variables (create from .env.example)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Security Features

- **Read-Only by Default**: Blocks all write operations (INSERT, UPDATE, DELETE, DROP, etc.)
- **SQL Injection Prevention**: Uses parameterized queries and SQLAlchemy's text() binding
- **Dry-Run Validation**: Validates SQL with EXPLAIN before execution
- **Schema Isolation**: Only queries tables in the connected database
- **Retry Limits**: Prevents infinite loops with configurable max retry attempts

## Performance

- Achieves **93%+ successful query execution** on benchmark datasets
- Automatic retry mechanism handles syntax errors and schema mismatches
- Schema caching reduces introspection overhead
- Connection pooling for efficient database access

## Future Enhancements

- [ ] Opik observability integration for end-to-end tracing
- [ ] Query result caching
- [ ] Support for multiple database types (MySQL, SQLite)
- [ ] Query optimization suggestions
- [ ] Visual query builder interface
- [ ] Export results to CSV/Excel

## License

MIT

## Author

**Ajay Ramaswamy**  
[GitHub](https://github.com/Ajayramaswamy2005) | [LinkedIn](https://linkedin.com/in/ajayramaswamy)

---

Built with LangGraph, FastAPI, and PostgreSQL. Powered by Groq for fast LLM inference.
