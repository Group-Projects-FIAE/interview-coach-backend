file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = file.read()
file.close()

CURRENT_MODE = None

def getSystemPrompt(user_input: str):
    system_prompt: str = SYSTEM_PROMPT
    formated_input = user_input.lower()

    if("/interview" in formated_input):
        CURRENT_MODE = "interview"
    elif("/quiz" in formated_input):
        CURRENT_MODE = "quiz"
    elif("/training" in formated_input):
        CURRENT_MODE = "training"
    
    file = open(CURRENT_MODE + '_prompt.txt', 'r')
    mode_prompt = file.read()
    file.close()

    if(CURRENT_MODE != None):
        system_prompt += mode_prompt
    
    return system_prompt
