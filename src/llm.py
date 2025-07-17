import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from src import config

def load_llm_and_tokenizer():
    """Loads the fine-tuned LLM and its tokenizer."""
    print("Logging into Hugging Face...")
    login(token=config.HUGGING_FACE_TOKEN)

    print("Loading LLM model (this may take a while)...")
    model = AutoModelForCausalLM.from_pretrained(
        config.LLM_MODEL_NAME,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        load_in_4bit=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL_NAME)
    print("LLM loaded successfully.")
    return model, tokenizer

def format_instruction(input_details, event):
    # Your prompt formatting logic
    return f"""... Your prompt template ..."""

def get_outfit_recommendation(prompt_r, event, model, tokenizer):
    """Generates outfit recommendations using the LLM."""
    # Your outfit_recommendation logic, taking model and tokenizer as arguments
    # ...
    # Return the cleaned text output
    return "This is a placeholder recommendation." # Replace with actual logic