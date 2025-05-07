from fastapi import FastAPI, HTTPException, Form, Depends, Request, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak.keycloak_admin import KeycloakAdmin
from llama_cpp.server.errors import ErrorResponse
from starlette import status
import logging
import sys
import traceback
from typing import Optional, Callable
from pydantic import BaseModel, Field
import mariadb
import uuid

from database.chat_history import save_chat_message
from database.job_description import create_job_description
from get_model_response import prompt_model_static, prompt_model_stream
from authentication.auth_controller import AuthController
from models import TokenResponse, UserInfo, SignUpRequest, LoginRequest
from authentication.auth_config import settings, keycloak_openid
from authentication.auth_service import AuthService
from database.sessions import create_session

# Configure logging at the start of the file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logging goes to stdout
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Interview Coach API")

# Initialize HTTPBearer security dependency
bearer_scheme = HTTPBearer()

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    logger.info(f"Incoming {request.method} request to {request.url}")
    logger.info(f"Request headers: {dict(request.headers)}")  # Changed to info level
    logger.info(f"Origin: {request.headers.get('origin')}")   # Log the origin header
    
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Log request body but mask sensitive data
                    body_str = body.decode()
                    if "password" in body_str:
                        # Simple password masking - you might want to make this more sophisticated
                        import json
                        body_dict = json.loads(body_str)
                        if "password" in body_dict:
                            body_dict["password"] = "********"
                        logger.info(f"Request body: {json.dumps(body_dict)}")  # Changed to info level
                    else:
                        logger.info(f"Request body: {body_str}")  # Changed to info level
            except Exception as e:
                logger.warning(f"Could not log request body: {str(e)}")
        
        response = await call_next(request)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")  # Changed to info level
        
        return response
        
    except Exception as e:
        logger.error(f"Unhandled error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}")
    logger.error(traceback.format_exc())
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Define CORS settings
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Add custom middleware for CORS debugging
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    logger.info(f"Request origin: {request.headers.get('origin')}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    
    return response

@app.post("/auth/signup", response_model=TokenResponse)
async def signup(request: SignUpRequest):
    try:
        logger.info("Signup request received")
        logger.info(f"Request data: {request.dict(exclude={'password'})}")
        
        token_response = AuthController.register(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name
        )
        logger.info("User registration successful")
        return token_response
            
    except HTTPException as he:
        logger.error(f"HTTP error during signup: {str(he)}")
        raise
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    try:
        logger.info("Login request received")
        logger.info(f"Email: {request.email}")
        
        token_response = AuthController.login(request.email, request.password)
        return token_response
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Log available routes
@app.on_event("startup")
async def startup_event():
    logger.info("=== Server Starting Up ===")
    logger.info("CORS Configuration:")
    # Find CORS middleware in the middleware stack
    cors_middleware = None
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, CORSMiddleware):
            cors_middleware = middleware
            break
    
    if cors_middleware:
        logger.info(f"Allowed Origins: {cors_middleware.options.get('allow_origins')}")
        logger.info(f"Allow Credentials: {cors_middleware.options.get('allow_credentials')}")
        logger.info(f"Allowed Methods: {cors_middleware.options.get('allow_methods')}")
        logger.info(f"Allowed Headers: {cors_middleware.options.get('allow_headers')}")
    else:
        logger.warning("CORS middleware not found in the stack")
    
    logger.info("Available Routes:")
    for route in app.routes:
        logger.info(f"{route.path} - {route.methods}")
    logger.info("=== Server Started Successfully ===")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the server is running and processing requests"""
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

class ChatRequest(BaseModel):
    sessionId: str
    userInput: str

class SessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="The session ID to create")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

@app.get("/")
def read_root():
    return AuthController.read_root()

### Chat Endpoints ###
@app.post("/chat")
async def chat(request: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        logger.info(f"Processing chat request for session: {request.sessionId}")
        
        if not request.userInput.strip():
            raise HTTPException(
                status_code=400,
                detail="Input cannot be empty."
            )
        
        # Verify token and get user info
        user_info = AuthController.protected_endpoint(credentials)
        
        response = prompt_model_static(request.sessionId, request.userInput)
        
        # Save chat messages
        save_chat_message(request.sessionId, True, request.userInput)
        save_chat_message(request.sessionId, False, response["response"])

        logger.info(f"Chat response generated successfully for session: {request.sessionId}")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP error in chat endpoint: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message: {str(e)}"
        )

# Unstable
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not request.userInput.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    
    # Verify token and get user info
    user_info = AuthController.protected_endpoint(credentials)
    
    return StreamingResponse(prompt_model_stream(request.sessionId, request.userInput), media_type="text/plain")


### Database Endpoints ###
@app.get("/chat/history/{session_id}", responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_history(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Verify token and get user info
        user_info = AuthController.protected_endpoint(credentials)
        return get_chat_history(session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )

@app.get("/chat/job-description/{session_id}", responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def get_description(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Verify token and get user info
        user_info = AuthController.protected_endpoint(credentials)
        return get_job_description(session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get job description"
        )

@app.post("/chat/job-description", responses={
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
async def create_new_job_description(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        # Verify token and get user info
        user_info = AuthController.protected_endpoint(credentials)
        return create_job_description(session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job description: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create job description"
        )

@app.post("/session")
async def create_new_session(session_id: str = Query(..., min_length=1, description="The session ID to create"), credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        logger.info(f"Creating new session with session_id: {session_id}")
        
        # Verify token and get user info
        user_info = AuthController.protected_endpoint(credentials)
        logger.info(f"User info retrieved: {user_info}")
        
        if not user_info or not user_info.preferred_username:
            logger.error("Invalid user info received")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user information"
            )
        
        # Create the session with user_id from the authenticated user
        success = create_session(session_id, user_info.preferred_username)
        
        if not success:
            logger.error("Failed to create session: No success returned")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create session: {str(e)}"
            )
        
        logger.info(f"Session created successfully: {session_id}")
        return {"status": "success", "message": "Session created successfully", "session_id": session_id}
        
    except mariadb.Error as e:
        logger.error(f"Database error creating session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except HTTPException as e:
        logger.error(f"HTTP error creating session: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )

@app.post("/test-model/stream")
async def test_model_stream(request: Request):
    data = await request.json()
    user_input = data.get("userInput", "")
    session_id = data.get("sessionId") or str(uuid.uuid4())
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    return StreamingResponse(prompt_model_stream(session_id, user_input), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
