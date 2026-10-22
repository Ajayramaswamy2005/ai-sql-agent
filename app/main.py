from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.models.schemas import QueryRequest, QueryResponse, SchemaResponse, HealthResponse
from app.agent.graph import agent_graph
from app.database.schema import get_schema_info, get_table_names
from app.database.connection import engine
from app.memory.store import memory

app = FastAPI(
    title="AI SQL Agent",
    description="Natural language to SQL agent powered by LangGraph and Groq",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    try:
        history = memory.get_history(request.session_id)
        memory.add_message(request.session_id, "user", request.query)

        initial_state = {
            "messages": [],
            "user_query": request.query,
            "schema_info": "",
            "generated_sql": "",
            "sql_result": {},
            "validation_error": None,
            "retry_count": 0,
            "conversation_history": history,
            "final_answer": "",
        }

        final_state = agent_graph.invoke(initial_state)

        result = final_state.get("sql_result", {})
        response = QueryResponse(
            session_id=request.session_id,
            user_query=request.query,
            generated_sql=final_state.get("generated_sql", ""),
            answer=final_state.get("final_answer", ""),
            columns=result.get("columns", []),
            rows=result.get("rows", []),
            row_count=result.get("row_count", 0),
            success=result.get("success", False),
            retry_count=final_state.get("retry_count", 0),
            error=result.get("error"),
        )

        memory.add_message(request.session_id, "assistant", response.answer)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema", response_model=SchemaResponse)
def schema():
    try:
        tables = get_table_names()
        schema_info = get_schema_info()
        return SchemaResponse(tables=tables, schema_info=schema_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
def health():
    db_connected = False
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        model=settings.groq_model,
    )


@app.delete("/memory/{session_id}")
async def clear_memory(session_id: str):
    memory.clear_session(session_id)
    return {"message": f"Session {session_id} cleared"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
