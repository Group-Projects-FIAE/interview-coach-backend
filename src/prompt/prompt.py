file = open('system_prompt.txt', 'r')
SYSTEM_PROMPT = file.read()
file.close()

def getSystemPrompt(user_input: str):
    system_prompt: str = SYSTEM_PROMPT

    if("/interview" in user_input):
        file = open('interview_prompt.txt', 'r')
        interview_prompt = file.read()
        file.close()
        system_prompt += interview_prompt
        return system_prompt
    elif("/quiz" in user_input):
        return system_prompt
    elif("/training" in user_input):
        return system_prompt
    else:
        return system_prompt
