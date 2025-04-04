from fastapi import FastAPI
from .routes.user import user_router  # Correct relative import

app = FastAPI()

# Include the user router
app.include_router(user_router)

# Additional routers can be added here in the future
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}