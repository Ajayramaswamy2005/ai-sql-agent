import asyncio
import json
from mcp.server import MCPServer
from mcp.types import TextContent

from app.agent.graph import agent_graph
from app.database.schema import get_schema_info, get_table_names
from app.memory.store import memory

server = MCPServer("ai-sql-agent")


@server.tool("query_database")
async def query_database(query: str, session_id: str = "default") -> list[TextContent]:
    if not query:
        return [TextContent(type="text", text="Error: 'query' parameter is required.")]

    try:
        history = memory.get_history(session_id)
        memory.add_message(session_id, "user", query)

        initial_state = {
            "messages": [],
            "user_query": query,
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
        memory.add_message(session_id, "assistant", final_state.get("final_answer", ""))

        response = {
            "session_id": session_id,
            "user_query": query,
            "generated_sql": final_state.get("generated_sql", ""),
            "answer": final_state.get("final_answer", ""),
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
            "row_count": result.get("row_count", 0),
            "success": result.get("success", False),
            "retry_count": final_state.get("retry_count", 0),
            "error": result.get("error"),
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2, default=str))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@server.tool("get_schema")
async def get_schema() -> list[TextContent]:
    try:
        schema = get_schema_info()
        return [TextContent(type="text", text=schema)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@server.tool("list_tables")
async def list_tables() -> list[TextContent]:
    try:
        tables = get_table_names()
        return [TextContent(type="text", text=json.dumps(tables, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@server.tool("clear_memory")
async def clear_memory(session_id: str) -> list[TextContent]:
    memory.clear_session(session_id)
    return [TextContent(type="text", text=f"Session '{session_id}' memory cleared.")]


async def run_mcp_server():
    await server.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
