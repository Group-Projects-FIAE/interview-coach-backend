from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import get_model_response

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/chat/{prompt}")
def get_response_static(prompt: str):
    print("Prompt:", prompt)
    response = get_model_response.prompt_model_static(prompt)
    print("Response:", response)
    return response

@app.get("/chat/stream/{prompt}")
async def get_response_stream(prompt: str):
    print("Prompt:", prompt)
    print("Response Stream:")
    return StreamingResponse(get_model_response.prompt_model_stream(prompt), media_type="text/plain")
    