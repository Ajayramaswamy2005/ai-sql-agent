from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import (
    discover_schema,
    generate_sql,
    validate_sql,
    execute_query,
    retry_sql,
    generate_answer,
)
from app.config import settings


def should_retry(state: AgentState) -> str:
    if state.get("retry_count", 0) >= settings.max_retry_attempts:
        return "max_retries"
    if state.get("validation_error"):
        return "retry"
    return "execute"


def check_execution(state: AgentState) -> str:
    result = state.get("sql_result", {})
    if result.get("success"):
        return "answer"
    if state.get("retry_count", 0) < settings.max_retry_attempts:
        return "retry"
    return "end"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("discover_schema", discover_schema)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("execute_query", execute_query)
    graph.add_node("retry_sql", retry_sql)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "discover_schema")
    graph.add_edge("discover_schema", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")

    graph.add_conditional_edges(
        "validate_sql",
        should_retry,
        {
            "retry": "retry_sql",
            "execute": "execute_query",
            "max_retries": "generate_answer",
        },
    )

    graph.add_edge("retry_sql", "validate_sql")

    graph.add_conditional_edges(
        "execute_query",
        check_execution,
        {
            "answer": "generate_answer",
            "retry": "retry_sql",
            "end": "generate_answer",
        },
    )

    graph.add_edge("generate_answer", END)

    return graph.compile()


agent_graph = build_graph()
