## Setup 
First install requirements.text using

```pip install -r requirements.txt```

You need to install the model manually, and put it into the src folder.

[Model name: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf](https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf?download=true)

## Running the API Server locally
To run the project enter following command

```uvicorn main:app --reload```
