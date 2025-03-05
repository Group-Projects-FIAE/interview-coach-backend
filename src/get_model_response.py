import setup_llama
from fastapi import HTTPException
from collections import defaultdict

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
#store chat session using a simple in memory dictionary
chat_sessions = defaultdict(lambda: {"history" : []})

chat_sessions = {}  # Ensure this is globally accessible

def get_chat_history(session_id: str):
    """Retrieve chat session or create a new one."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {"history": [], "job_description": None}
    return chat_sessions[session_id]

def store_job_description(session_id: str, user_input: str):
    session = get_chat_history(session_id)
    session["job_description"] = user_input
    session["history"].append(f"User provided Job Description: {user_input}")
    print(f"Job Description Stored for Session {session_id}")

def prompt_model_static(session_id: str, user_input: str):
    """Handles non-streaming AI responses."""
    print(f"📩 Received request: session_id={session_id}, user_input={user_input}")

    session = get_chat_history(session_id)
    chat_history = session["history"]
    job_description = session.get("job_description", None)

    # Fix: Store first user input as job description
    if job_description is None:
        store_job_description(session_id, user_input)
        return {"response": "Thank you for providing the job description. What would you like to do next?"}

    chat_history.append(f"User: {user_input}")
    conversation = f"<<SYS>>\n{SYSTEM_PROMPT}\nJob Description: {job_description}\n<</SYS>>\n\n" + "\n".join(chat_history)

    print(f"📝 Sending to model: {conversation[:500]}...")  # Log first 500 characters

    # Call LLM model for response
    token_budget = max(200, min(600, 4096 - len(conversation.split())))
    response = model(conversation, max_tokens=token_budget)

    # Validate response
    if "choices" not in response or not response["choices"]:
        print("Error: LLM did not return a valid response!")
        raise HTTPException(status_code=500, detail="LLM did not return a valid response.")

    ai_response = response["choices"][0]["text"].strip()

    # Update chat history
    chat_history.append(f"AI: {ai_response}")
    print(f"AI Response: {ai_response}")

    return {"response": ai_response}


async def prompt_model_stream(session_id: str, user_input: str):
    print(f"📩 Received request: session_id={session_id}, user_input={user_input}")

    session = get_chat_history(session_id)  # Retrieve chat history
    chat_history = session["history"]

    chat_history.append(f"User: {user_input}")
    conversation = f"<<SYS>>\n{SYSTEM_PROMPT}\n<</SYS>>\n\n" + "\n".join(chat_history)

    print(f"📝 Sending to model: {conversation[:500]}...")  # Log first 500 chars

    response = model(conversation, max_tokens=200, stream=True)
    print(f"🔄 Model started streaming response...")

    full_response = ""
    async for chunk in response:
        text_chunk = chunk["choices"][0]["text"]
        full_response += text_chunk
        yield text_chunk  # Send to frontend immediately

    print(f"✅ Model finished. Full response: {full_response[:500]}...")
    chat_sessions[session_id]["history"].append(f"AI: {full_response}")