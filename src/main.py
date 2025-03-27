from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.responses import StreamingResponse
from get_model_response import prompt_model_static, prompt_model_stream
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import database.setup_maria_db
from database.sessions import create_session
from database.chat_history import save_chat_message, get_chat_history
from database.job_description import create_job_description, get_job_description
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import TokenResponse, UserInfo
from authentication.auth_controller import AuthController

app = FastAPI()

bearer_scheme = HTTPBearer()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    sessionId: str
    userInput: str

class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/")
def read_root():
    return AuthController.read_root()

### Chat Enpoints ###
@app.get("/chat")
async def chat(session_id: str, user_input: str):
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    response = prompt_model_static(session_id, user_input)
    
    # Save chat messages
    save_chat_message(session_id, True, user_input)
    save_chat_message(session_id, False, response)

    return response

# Unstable
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.userInput.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    
    return StreamingResponse(prompt_model_stream(request.sessionId, request.userInput), media_type="text/plain")


### Database Endpoints ###
@app.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    return get_chat_history(session_id)

@app.get("/chat/jobdescription/{session_id}")
async def get_description(session_id: str):
    return get_job_description(session_id)

@app.post("/chat/jobdescription")
async def create_new_job_description(session_id: str):
    return create_job_description(session_id)

@app.post("/session")
async def create_new_session(session_id: str):
    return create_session(session_id)


### Authentication Endpoints ###
@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint to authenticate the user and return an access token.

    Args:
        request: LoginRequest: Contains credentials.

    Returns:
        TokenResponse: Contains the access token upon successful authentication.
    """
    print("test")
    return AuthController.login(request.email, request.password)

# Handle protected enpoints like this later
@app.get("/protected", response_model=UserInfo)
async def protected_endpoint(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Protected endpoint that requires a valid token for access.

    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token provided via HTTP Authorization header.

    Returns:
        UserInfo: Information about the authenticated user.
    """

    # Checks the users bearer token
    user_info = AuthController.protected_endpoint(credentials)
    
    return user_info
