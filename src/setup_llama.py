from llama_cpp import Llama

def setup_model(core_count, batch_size, context_size):
    llm = Llama(
        model_path="Meta-Llama-3.1-8B-Instruct-Q3_K_L.gguf",
        n_threads=core_count,   # CPU Cores used
        n_batch=batch_size,     # Batch size, should be a square of 2
        n_ctx=context_size,     # Context size, should be a square of 2
        verbose=False           # Suppress output
    )
    return llm
