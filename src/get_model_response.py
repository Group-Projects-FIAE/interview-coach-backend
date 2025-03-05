import setup_llama

file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = file.read()
file.close()

'''
Model prompt structure:

<<SYS>> system_prompt <</SYS>>
User: user_prompt
Assistant:
'''

model = setup_llama.setup_model(8, 512, 2048)

def prompt_model_static(user_prompt):
    response = model(get_model_prompt(user_prompt), max_tokens=100, stop=["</s>", "[INST]", "\n"])
    return {"response": response["choices"][0]["text"]}

async def prompt_model_stream(user_prompt):
    response = model(get_model_prompt(user_prompt), max_tokens=100, stream=True, stop=["</s>", "[INST]", "\n"])

    for chunk in response:
        print(chunk["choices"][0]["text"])
        yield chunk["choices"][0]["text"]

def get_model_prompt(user_prompt):
    model_prompt = f"<<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>\n\nUser: {user_prompt}\n\nAssistant:"
    print(model_prompt)
    return model_prompt
    