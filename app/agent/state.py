from typing import Annotated, Any
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_query: str
    schema_info: str
    generated_sql: str
    sql_result: dict[str, Any]
    validation_error: str | None
    retry_count: int
    conversation_history: list[dict[str, str]]
    final_answer: str
