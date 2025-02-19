from fastapi import FastAPI

app = FastAPI()

file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = file.read()
print(SYSTEM_PROMPT)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

