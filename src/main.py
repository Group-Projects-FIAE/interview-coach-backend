from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from get_model_response import prompt_model_static, prompt_model_stream
import setup_maria_db
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

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
    return {"message": "Hello, FastAPI!"}

@app.get("/chat")
async def chat(session_id: str, user_input: str):
    if not user_input.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")

    return prompt_model_static(session_id, user_input)

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.userInput.strip():
        raise HTTPException(status_code=400, detail="User input cannot be empty.")
    
    return StreamingResponse(prompt_model_stream(request.sessionId, request.userInput), media_type="text/plain")
