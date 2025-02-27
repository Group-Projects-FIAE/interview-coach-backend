import setup_llama

file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = file.read()
model = setup_llama.setup_model(8, 512, 2048)

def prompt_model_static(prompt):
    final_prompt = f"[INST] <<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n{prompt} [/INST]"
    response = model(final_prompt, max_tokens=200)
    return {"response": response["choices"][0]["text"]}

async def prompt_model_stream(prompt):
    final_prompt = f"[INST] {SYSTEM_PROMPT}\n\n{prompt} [/INST]"
    response = model(final_prompt, max_tokens=100, stream=True)

    for chunk in response:
        print(chunk["choices"][0]["text"])
        yield chunk["choices"][0]["text"]
