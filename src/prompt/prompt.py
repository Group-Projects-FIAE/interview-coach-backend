from pathlib import Path

# Define the base directory
BASE_DIR = Path(__file__).parent

# Read system prompt
file_path = BASE_DIR / 'system_prompt.txt'
with file_path.open('r', encoding='utf-8') as file:
    SYSTEM_PROMPT = file.read()

global CURRENT_MODE

def get_system_prompt(user_input: str):
    global CURRENT_MODE
    system_prompt: str = SYSTEM_PROMPT
    formatted_input = user_input.lower()

    if("/interview" in formatted_input):
        CURRENT_MODE = "interview"
    elif("/quiz" in formatted_input):
        CURRENT_MODE = "quiz"
    elif("/training" in formatted_input):
        CURRENT_MODE = "training"
    else:
        CURRENT_MODE = None

    if CURRENT_MODE is not None:
        file = open("prompt/" + CURRENT_MODE + '_prompt.txt', 'r')
        mode_prompt = file.read()
        file.close()
        system_prompt += mode_prompt
    
    return system_prompt