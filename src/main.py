from fastapi import FastAPI, HTTPException, Form, Depends
from fastapi.responses import StreamingResponse
from get_model_response import prompt_model_static, prompt_model_stream
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import setup_maria_db
from chat_history import save_chat_message, get_chat_history
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models import TokenResponse, UserInfo
from auth_controller import AuthController

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

@app.get("/")
def read_root():
    return AuthController.read_root()

@app.get("/chat")
async def chat(session_id: str, user_input: str):
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    response = prompt_model_static(session_id, user_input)
    
    # Save chat messages
    save_chat_message(session_id, True, user_input)
    save_chat_message(session_id, False, response)

    return response

@app.get("/chat/history")
async def get_history(session_id: str):
    return get_chat_history(session_id)

# Unstable
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.userInput.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    
    return StreamingResponse(prompt_model_stream(request.sessionId, request.userInput), media_type="text/plain")

@app.post("/login", response_model=TokenResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    """
    Login endpoint to authenticate the user and return an access token.

    Args:
        username (str): The username of the user attempting to log in.
        password (str): The password of the user.

    Returns:
        TokenResponse: Contains the access token upon successful authentication.
    """
    return AuthController.login(username, password)

# Handle chats like this later
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
    
    # ...
    
    return user_info
