from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from routers import auth, v2_tasks, tasks, users


def custom_openapi():
    """Hide and endpoint."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom API",
        description="My Custom API",
        version=".0",
        routes=app.routes,
    )
    del openapi_schema["paths"]["/auth/token"]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="Task Manager API",
    description="This is a task management API",
    version="1.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(v2_tasks.router)
