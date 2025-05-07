import setup_llama
from fastapi import HTTPException
from collections import defaultdict
from prompt.prompt import get_system_prompt
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = setup_llama.setup_model(8, 512, 2048)
#store chat session using a simple in memory dictionary
chat_sessions = defaultdict(lambda: {
    "history": [],
    "job_description": None,
    "is_interview_mode": False,
    "interview_state": None,  # None, 'in_progress', 'finished'
    "questions_asked": 0,
    "max_questions": 5,  # adjust this
    "summary_points": []
})

LLAMA3_SYSTEM = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{}\n<|eot_id|>"
LLAMA3_USER = "<|start_header_id|>user<|end_header_id|>\n{}\n<|eot_id|>"
LLAMA3_ASSISTANT = "<|start_header_id|>assistant<|end_header_id|>\n{}\n<|eot_id|>"


def get_chat_history(session_id: str):
    """Retrieve chat session or create a new one."""
    try:
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "history": [],
                "job_description": None,
                "is_interview_mode": False,
                "interview_state": None,
                "questions_asked": 0,
                "max_questions": 3,
                "summary_points": []
            }
        return chat_sessions[session_id]
    except Exception as e:
        logger.error(f"Error retrieving chat history for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

def validate_interview_response(response: str) -> str:
    # Remove any text that appears to be a user response
    user_response_patterns = [
        r"User:.*?(?=\n|$)",
        r"Candidate:.*?(?=\n|$)",
        r"I would.*?(?=\n|$)",
        r"Let me.*?(?=\n|$)",
        r"First,.*?(?=\n|$)",
        r"To answer.*?(?=\n|$)",
        r"Regarding.*?(?=\n|$)",
        r"As a.*?(?=\n|$)",
    ]
    for pattern in user_response_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)
    response = "\n".join(line for line in response.split("\n") if line.strip())
    return response.strip()

def store_job_description(session_id: str, user_input: str):
    try:
        session = get_chat_history(session_id)
        session["job_description"] = user_input
        session["history"].append(f"User provided Job Description: {user_input}")
        logger.info(f"Job Description Stored for Session {session_id}")
    except Exception as e:
        logger.error(f"Error storing job description for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store job description")

def build_llama3_prompt(session, user_input, ai_response=None):
    # Compose the system prompt
    system_prompt = get_system_prompt(user_input)
    job_description = session["job_description"]
    prompt = LLAMA3_SYSTEM.format(system_prompt + f"\nJob Description: {job_description}")
    # Add conversation history
    for entry in session["history"]:
        if entry.startswith("User: "):
            prompt += LLAMA3_USER.format(entry[6:])
        elif entry.startswith("AI: "):
            prompt += LLAMA3_ASSISTANT.format(entry[4:])
    # Add current user input
    prompt += LLAMA3_USER.format(user_input)
    # Optionally add last AI response (for streaming)
    if ai_response:
        prompt += LLAMA3_ASSISTANT.format(ai_response)
    return prompt

def extract_summary_points(text):
    # Extract bullet points from summary
    code_block = re.search(r"```[\s\S]*?```", text)
    if code_block:
        content = code_block.group(0)
        return content
    # fallback: try to extract lines starting with -
    lines = [line for line in text.splitlines() if line.strip().startswith("-")]
    if lines:
        return "```\n" + "\n".join(lines) + "\n```"
    return "```No summary generated.\n```"

def prompt_model_static(session_id: str, user_input: str):
    try:
        logger.info(f"Received request: session_id={session_id}, user_input={user_input}")
        session = get_chat_history(session_id)
        chat_history = session["history"]
        job_description = session.get("job_description", None)
        is_interview_mode = session.get("is_interview_mode", False)
        interview_state = session.get("interview_state", None)
        questions_asked = session.get("questions_asked", 0)
        max_questions = session.get("max_questions", 3)
        summary_points = session.get("summary_points", [])

        # Handle /q quit command
        if user_input.strip().lower() == "/q":
            session["is_interview_mode"] = False
            session["interview_state"] = None
            session["questions_asked"] = 0
            session["summary_points"] = []
            chat_history.append(f"User: {user_input}")
            quit_message = (
                "You have exited all modes. Available commands:\n"
                "/interview - Start interview simulation\n"
                "/quiz - Start quiz mode\n"
                "/training - Start training mode\n"
                "/selfcheck - Self check mode\n"
                "/help - List all commands\n\n"
                "Please enter a command to begin."
            )
            chat_history.append(f"AI: {quit_message}")
            return {"response": quit_message}

        # Check if this is an interview command
        if "/interview" in user_input.lower():
            session["is_interview_mode"] = True
            session["interview_state"] = "in_progress"
            session["questions_asked"] = 0
            session["summary_points"] = []
            chat_history.append(f"User: {user_input}")
            logger.info("Calling model for first interview question...")
            prompt = build_llama3_prompt(session, user_input)
            token_budget = max(200, min(600, 4096 - len(prompt.split())))
            response = model(prompt, max_tokens=token_budget)
            logger.info(f"Raw model response: {response}")
            if "choices" not in response or not response["choices"]:
                logger.error("LLM did not return a valid response!")
                raise HTTPException(status_code=500, detail="LLM did not return a valid response.")
            ai_response = response["choices"][0]["text"].strip()
            ai_response = validate_interview_response(ai_response)
            logger.info(f"First interview model output: {ai_response}")
            if not ai_response:
                logger.warning("Model returned empty response, using fallback question.")
                ai_response = "Let's begin the interview. Can you tell me about a challenging project you worked on and how you overcame it?"
            session["questions_asked"] += 1
            chat_history.append(f"AI: {ai_response}")
            logger.info(f"AI Response generated for session {session_id}")
            return {"response": ai_response}

        # Store first user input as job description
        if job_description is None:
            store_job_description(session_id, user_input)
            return {"response": "Thank you for providing the job description. What would you like to do next?"}

        # If in interview mode, enforce strict logic
        if session["is_interview_mode"]:
            # If interview just started or in progress
            if session["interview_state"] == "in_progress":
                # Add user input to history
                chat_history.append(f"User: {user_input}")
                # Build prompt for Llama 3
                prompt = build_llama3_prompt(session, user_input)
                token_budget = max(200, min(600, 4096 - len(prompt.split())))
                response = model(prompt, max_tokens=token_budget)
                if "choices" not in response or not response["choices"]:
                    logger.error("LLM did not return a valid response!")
                    raise HTTPException(status_code=500, detail="LLM did not return a valid response.")
                ai_response = response["choices"][0]["text"].strip()
                ai_response = validate_interview_response(ai_response)
                # If this is the last question, mark as finished and add summary
                session["questions_asked"] += 1
                if session["questions_asked"] >= max_questions:
                    session["interview_state"] = "finished"
                    # Extract summary points
                    summary = extract_summary_points(ai_response)
                    session["summary_points"].append(summary)
                    ai_response += f"\n\nHere is your interview summary:\n{summary}"
                # Add AI response to history
                chat_history.append(f"AI: {ai_response}")
                logger.info(f"AI Response generated for session {session_id}")
                return {"response": ai_response}
            elif session["interview_state"] == "finished":
                return {"response": "The interview has concluded. If you want to start over, type /interview again."}
        # Not in interview mode: normal chat
        chat_history.append(f"User: {user_input}")
        prompt = build_llama3_prompt(session, user_input)
        token_budget = max(200, min(600, 4096 - len(prompt.split())))
        response = model(prompt, max_tokens=token_budget)
        if "choices" not in response or not response["choices"]:
            logger.error("LLM did not return a valid response!")
            raise HTTPException(status_code=500, detail="LLM did not return a valid response.")
        ai_response = response["choices"][0]["text"].strip()
        chat_history.append(f"AI: {ai_response}")
        logger.info(f"AI Response generated for session {session_id}")
        return {"response": ai_response}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prompt_model_static: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")


async def prompt_model_stream(session_id: str, user_input: str):
    try:
        logger.info(f"Received streaming request: session_id={session_id}, user_input={user_input}")
        session = get_chat_history(session_id)
        chat_history = session["history"]
        job_description = session.get("job_description", None)
        is_interview_mode = session.get("is_interview_mode", False)
        interview_state = session.get("interview_state", None)
        questions_asked = session.get("questions_asked", 0)
        max_questions = session.get("max_questions", 3)
        summary_points = session.get("summary_points", [])

        # Handle /q quit command
        if user_input.strip().lower() == "/q":
            session["is_interview_mode"] = False
            session["interview_state"] = None
            session["questions_asked"] = 0
            session["summary_points"] = []
            chat_history.append(f"User: {user_input}")
            quit_message = (
                "You have exited all modes. Available commands:\n"
                "/interview - Start interview simulation\n"
                "/quiz - Start quiz mode\n"
                "/training - Start training mode\n"
                "/selfcheck - Self check mode\n"
                "/help - List all commands\n\n"
                "Please enter a command to begin."
            )
            chat_history.append(f"AI: {quit_message}")
            yield quit_message
            return

        if job_description is None:
            store_job_description(session_id, user_input)
            yield "Thank you for providing the job description. What would you like to do next?"
            return

        if session["is_interview_mode"]:
            if session["interview_state"] == "in_progress":
                chat_history.append(f"User: {user_input}")
                prompt = build_llama3_prompt(session, user_input)
                response = model(prompt, max_tokens=200, stream=True)
                logger.info(f"Model started streaming response for session {session_id}")
                full_response = ""
                try:
                    async for chunk in response:
                        if "choices" not in chunk or not chunk["choices"]:
                            logger.error("Invalid chunk received from model")
                            continue
                        text_chunk = chunk["choices"][0]["text"]
                        full_response += text_chunk
                        yield text_chunk
                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}")
                    yield f"\n[Error: Streaming interrupted. Please try again.]"
                session["questions_asked"] += 1
                if session["questions_asked"] >= max_questions:
                    session["interview_state"] = "finished"
                    summary = extract_summary_points(full_response)
                    session["summary_points"].append(summary)
                    yield f"\n\nHere is your interview summary:\n{summary}"
                chat_sessions[session_id]["history"].append(f"AI: {full_response}")
                return
            elif session["interview_state"] == "finished":
                yield "The interview has concluded. If you want to start over, type /interview again."
                return
        # Not in interview mode: normal chat
        chat_history.append(f"User: {user_input}")
        prompt = build_llama3_prompt(session, user_input)
        response = model(prompt, max_tokens=200, stream=True)
        logger.info(f"Model started streaming response for session {session_id}")
        full_response = ""
        try:
            async for chunk in response:
                if "choices" not in chunk or not chunk["choices"]:
                    logger.error("Invalid chunk received from model")
                    continue
                text_chunk = chunk["choices"][0]["text"]
                full_response += text_chunk
                yield text_chunk
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            yield f"\n[Error: Streaming interrupted. Please try again.]"
        chat_sessions[session_id]["history"].append(f"AI: {full_response}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prompt_model_stream: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate streaming response")