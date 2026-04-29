from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
from app.core.database import test_db_connection, create_tables
from app.core.exceptions import DatabaseError
from app.schemas.message_schema import MessageRequest, MessageResponse
from app.controllers.message_controller import MessageController
from app.api import task_slot_routes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting up application...")
    
    try:
        test_db_connection()
        logger.info("Creating database tables...")
        create_tables()
    except DatabaseError as e:
        logger.error(f"Failed to initialize database: {e.message}")
        logger.warning("Application started but database is unavailable!")
    
    yield
    
    logger.info("Shutting down application...")

app = FastAPI(
    title="Workload Prioritizer API", 
    version="1.0.0",
    lifespan=lifespan
)

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",      # Alternative
        "http://localhost:8000",      # Backend itself
        "http://127.0.0.1:8000",      # Alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],              # อนุญาตทุก HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],              # อนุญาตทุก headers
)

# Register API Routes
app.include_router(task_slot_routes.router, prefix="/api", tags=["Task Slots"])

@app.get("/")
def read_root():
    return {"message": "Hello from Workload Prioritizer Backend!"}

@app.get("/ping")
def ping_system():
    return {"status": "success", "detail": "pong!"}

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.errors()} - {request.url}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": 422,
            "message": "Validation failed",
            "errors": exc.errors(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    logger.error(f"Database error: {exc.message} - {request.url}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "error",
            "code": 503,
            "message": "Database service unavailable",
            "detail": exc.message,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unexpected error: {str(exc)} - {request.url}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "code": 500,
            "message": "Internal server error",
            "path": str(request.url.path)
        }
    )


# Initialize Controller
message_controller = MessageController()


# API Endpoints
@app.post("/api/echo", response_model=MessageResponse)
def echo_message(request_body: MessageRequest):
    """
    Echo API endpoint that receives a message and returns it as a result
    """
    return message_controller.echo_message(request_body)
