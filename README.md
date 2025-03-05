## Setup 
First install requirements.text using

```pip install -r requirements.txt```

You need to install the model manually, and put it into the src folder.

[Model name: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf](https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf?download=true)

## Running the API Server locally
To run the project enter following command

```uvicorn main:app --reload```

## Troubleshooting
if the installation of llama-cpp-python runs into an error due to llama.cpp not recognizing std::chrono or similar (see this: https://github.com/abetlen/llama-cpp-python/issues/1942), then follow the collowing steps


(steps from here: https://github.com/abetlen/llama-cpp-python/issues/1942#issuecomment-2685943185)
``` 
# clone llama-cpp-python in any directory 
git clone --recurse-submodules https://github.com/abetlen/llama-cpp-python.git
cd llama-cpp-python

# update to latest llama.cpp (this pulls in all llama.cpp changes not just the fix needed for MSVC, so may have other effects as well)
git submodule update --remote vendor\llama.cpp

# Upgrade pip (required for editable mode)
pip install --upgrade pip

# Install with pip
# inside VS Code, switch to directory of llama-cpp-python, then run
pip install -e .
```