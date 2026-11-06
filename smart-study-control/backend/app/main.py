from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.db.session import SessionLocal
from app.security.request_size import RequestSizeLimit
from app.api.access import router as access_router
from app.api.location import router as location_router
from app.api.routes import router
from app.api.reading import router as reading_router
from app.api.automation import router as automation_router


@asynccontextmanager
async def lifespan(app):
    settings.validate()
    yield


app = FastAPI(title="SMART STUDY CONTROL", version="0.3.0", lifespan=lifespan)
app.add_middleware(RequestSizeLimit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.origins),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    allow_credentials=False,
)
app.include_router(router)
app.include_router(access_router)
app.include_router(location_router)
app.include_router(reading_router)
app.include_router(automation_router)


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(
        {"error": {"code": exc.status_code, "message": exc.detail}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # Do not echo passwords, tokens or submitted student data in error details.
    return JSONResponse(
        {
            "error": {
                "code": 422,
                "message": "Request validation failed",
                "fields": [{"location": list(e["loc"]), "message": e["msg"]} for e in exc.errors()],
            }
        },
        status_code=422,
    )


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        {"error": {"code": 409, "message": "Conflicting or duplicate resource"}}, status_code=409
    )


@app.middleware("http")
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/health/live", tags=["health"])
def live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1 FROM alembic_version LIMIT 1"))
        if settings.redis_url:
            from app.security.rate_limit import client

            client.ping()
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {"status": "ready"}
