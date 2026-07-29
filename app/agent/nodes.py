from langchain_groq import ChatGroq
from app.agent.state import AgentState
from app.agent.prompts import (
    SYSTEM_PROMPT,
    VALIDATION_PROMPT,
    ANSWER_PROMPT,
    RETRY_PROMPT,
)
from app.database.schema import get_schema_info
from app.database.connection import execute_sql, validate_sql_dry_run
from app.config import settings


llm = ChatGroq(
    api_key=settings.groq_api_key,
    model=settings.groq_model,
    temperature=0,
)


def discover_schema(state: AgentState) -> dict:
    schema = get_schema_info()
    return {"schema_info": schema}


def generate_sql(state: AgentState) -> dict:
    history_text = ""
    if state.get("conversation_history"):
        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in state["conversation_history"][-6:]
        )

    prompt = SYSTEM_PROMPT.format(schema=state["schema_info"])
    if history_text:
        prompt += f"\n\nCONVERSATION HISTORY:\n{history_text}"
    prompt += f"\n\nUSER QUESTION: {state['user_query']}"

    response = llm.invoke(prompt)
    sql = response.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return {"generated_sql": sql}


def validate_sql(state: AgentState) -> dict:
    sql = state["generated_sql"]

    dangerous_keywords = ["DELETE", "DROP", "TRUNCATE", "ALTER", "INSERT", "UPDATE", "CREATE"]
    sql_upper = sql.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return {
                "validation_error": f"Blocked: {keyword} statements are not allowed.",
                "generated_sql": "",
            }

    error = validate_sql_dry_run(sql)
    if error:
        return {"validation_error": error}

    return {"validation_error": None}


def execute_query(state: AgentState) -> dict:
    sql = state["generated_sql"]
    try:
        columns, rows = execute_sql(sql)
        result = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "success": True,
        }
        return {"sql_result": result}
    except Exception as e:
        return {
            "sql_result": {"success": False, "error": str(e)},
            "validation_error": str(e),
        }


def retry_sql(state: AgentState) -> dict:
    retry_count = state.get("retry_count", 0) + 1
    if retry_count > settings.max_retry_attempts:
        return {
            "retry_count": retry_count,
            "final_answer": f"Failed after {settings.max_retry_attempts} retry attempts. Last error: {state.get('validation_error', 'Unknown')}",
            "sql_result": {"success": False, "error": "Max retries exceeded"},
        }

    prompt = RETRY_PROMPT.format(
        schema=state["schema_info"],
        question=state["user_query"],
        previous_sql=state["generated_sql"],
        error=state.get("validation_error", "Unknown error"),
        attempt=retry_count,
        max_attempts=settings.max_retry_attempts,
    )

    response = llm.invoke(prompt)
    sql = response.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return {
        "generated_sql": sql,
        "retry_count": retry_count,
        "validation_error": None,
    }


def generate_answer(state: AgentState) -> dict:
    result = state.get("sql_result", {})

    if not result.get("success"):
        return {
            "final_answer": f"Query execution failed: {result.get('error', 'Unknown error')}"
        }

    rows = result.get("rows", [])
    columns = result.get("columns", [])

    if not rows:
        display_results = "No results found (empty result set)."
    else:
        display_rows = rows[:20]
        display_results = f"Columns: {columns}\n"
        display_results += "\n".join(str(row) for row in display_rows)
        if len(rows) > 20:
            display_results += f"\n... and {len(rows) - 20} more rows"

    prompt = ANSWER_PROMPT.format(
        question=state["user_query"],
        sql=state["generated_sql"],
        results=display_results,
    )

    response = llm.invoke(prompt)
    return {"final_answer": response.content.strip()}
