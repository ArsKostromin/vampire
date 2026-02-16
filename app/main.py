from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api import users

app = FastAPI()

# Подключаем роутер
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
def root():
    return {"message": "Vampire API is running"}


# Роуты, для которых в OpenAPI показывать Bearer (только защищённые)
PROTECTED_OPENAPI = {
    ("/users/me", "get"),
    ("/users/leaderboard", "get"),
    ("/users/record", "patch"),
}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Vampire API",
        version="1.0.0",
        description="API без паролей, только имя + JWT токены",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path_key, path_obj in openapi_schema["paths"].items():
        for method_key, method_spec in path_obj.items():
            if method_key in ("get", "post", "put", "patch", "delete"):
                if (path_key, method_key) in PROTECTED_OPENAPI:
                    method_spec["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
