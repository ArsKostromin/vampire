from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api import users
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Подключаем роутер
app.include_router(users.router, prefix="/users", tags=["users"])

# Простая защита для /docs через Bearer Token (без OAuth2 password flow)
auth_scheme = HTTPBearer()

@app.get("/")
def root():
    return {"message": "Vampire API is running"}

# Кастомизируем OpenAPI чтобы убрать OAuth2 PasswordBearer

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
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
