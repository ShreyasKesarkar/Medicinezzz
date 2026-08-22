from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.database import db
from app.api.routes import auth, medicines, schedules, timeline, events, doses, history

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB Pool
    await db.connect()
    yield
    # Shutdown: Close DB Pool
    await db.disconnect()

app = FastAPI(
    title="Medicinezzz API",
    version="1.0.0",
    lifespan=lifespan
)

from app.config import settings

# Configure CORS
allow_origin_regex = None
if settings.environment == "development":
    # Match any http://localhost or http://127.0.0.1 with any optional port for Flutter Web
    allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    allow_origins = []
else:
    if settings.allowed_origins:
        allow_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    else:
        allow_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(medicines.router, prefix="/api/v1/medicines", tags=["Medicines"])
app.include_router(schedules.router, prefix="/api/v1", tags=["Schedules"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["Timeline"])
app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(doses.router, prefix="/api/v1/doses", tags=["Doses"])
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])

# Global Exception Handlers for consistent API responses

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        code = detail["code"]
        message = detail["message"]
    else:
        code = "HTTP_ERROR"
        if exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 409:
            code = "CONFLICT"
        message = str(detail)
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Construct a readable error description
    err_msgs = []
    for e in errors:
        loc = ".".join(map(str, e["loc"]))
        err_msgs.append(f"{loc}: {e['msg']}")
    message = "Input validation failed: " + "; ".join(err_msgs)
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()  # Log stack trace in console
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred: {str(exc)}"
            }
        }
    )

@app.get("/")
async def root():
    return {"message": "Medicinezzz API is running."}

@app.get("/health")
async def health():
    return {"status": "ok"}
