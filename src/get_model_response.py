from scraper import scrape_for_job_description
import setup_llama
from fastapi import HTTPException
from collections import defaultdict
from prompt.prompt import getSystemPrompt
import re


model = setup_llama.setup_model(2, 512, 2048)
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

JOB_KEYWORDS = [
    "responsibilities", "qualifications", "we are looking for",
    "skills required", "your tasks", "requirements", "job description"
]

def looks_like_job_description(text: str):
    """Check for common job description phrases."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in JOB_KEYWORDS)

def is_url(text: str):
    """Basic check if text is a URL."""
    return re.match(r'^https?://', text) is not None

def prompt_model_static(session_id: str, user_input: str):
    """Handles non-streaming AI responses."""
    print(f"Received request: session_id={session_id}, user_input={user_input}")

    session = get_chat_history(session_id)
    chat_history = session["history"]
    job_description = session.get("job_description", None)

    if job_description is None:
        # Check if input is URL
        if is_url(user_input):
            try:
                jd = scrape_for_job_description(user_input)
                store_job_description(session_id, jd)
                return {"response": "Job description successfully extracted from URL. What would you like to do next?"}
            except Exception as e:
                print(f"Error scraping URL: {e}")
                return {"response": "Sorry, we couldn’t extract a job description from that URL. Please try again or paste the text directly."}

        # Check if input looks like a job description
        elif looks_like_job_description(user_input):
            store_job_description(session_id, user_input)
            return {"response": "Thank you for providing the job description. What would you like to do next?"}
        
        # Fallback: treat it as job description anyway
        else:
            store_job_description(session_id, user_input)
            return {"response": "Thanks! We’ve saved this as your job description. Let me know what you’d like to do next."}

    chat_history.append(f"User: {user_input}")
    system_prompt = getSystemPrompt(user_input)
    conversation = f"<<SYS>>\n{system_prompt}\nJob Description: {job_description}\n<</SYS>>\n\n" + "\n".join(chat_history)

    print(f"Sending to model: {conversation[:500]}...")  # Log first 500 characters

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
    print(f"Received request: session_id={session_id}, user_input={user_input}")

    session = get_chat_history(session_id)  # Retrieve chat history
    chat_history = session["history"]

    chat_history.append(f"User: {user_input}")
    system_prompt = getSystemPrompt(user_input)
    conversation = f"<<SYS>>\n{system_prompt}\n<</SYS>>\n\n" + "\n".join(chat_history)

    print(f"Sending to model: {conversation[:500]}...")  # Log first 500 chars

    response = model(conversation, max_tokens=200, stream=True)
    print(f"Model started streaming response...")

    full_response = ""
    async for chunk in response:
        text_chunk = chunk["choices"][0]["text"]
        full_response += text_chunk
        yield text_chunk  # Send to frontend immediately

    print(f"Model finished. Full response: {full_response[:500]}...")
    chat_sessions[session_id]["history"].append(f"AI: {full_response}")