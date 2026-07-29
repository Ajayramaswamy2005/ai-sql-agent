from collections import defaultdict
from threading import Lock


class ConversationMemory:
    def __init__(self, max_history: int = 20):
        self._store: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._lock = Lock()
        self._max_history = max_history

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._store[session_id].append({"role": role, "content": content})
            if len(self._store[session_id]) > self._max_history:
                self._store[session_id] = self._store[session_id][-self._max_history:]

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            return list(self._store.get(session_id, []))

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def clear_all(self) -> None:
        with self._lock:
            self._store.clear()


memory = ConversationMemory()
