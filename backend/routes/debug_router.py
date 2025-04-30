from fastapi import APIRouter
import threading

debug_router = APIRouter()

@debug_router.get("/debug/threads")
def list_threads():
    return {
        "threads": [
            {"name": t.name, "alive": t.is_alive()} for t in threading.enumerate()
        ]
    }
