from fastapi import FastAPI
import setup_llama

app = FastAPI()

file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = f"<<SYS>>\n{file.read()}\n<</SYS>>"
model = setup_llama.setup_model(8, 512, 2048)

def chat_with_llama(prompt):
    final_prompt = f"[INST] {SYSTEM_PROMPT}\n\n{prompt} [/INST]"
    response = model(final_prompt, max_tokens=200)
    return {"response": response["choices"][0]["text"]}

print(chat_with_llama("Hello!"))


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
