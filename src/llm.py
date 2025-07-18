import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, BitsAndBytesConfig
from huggingface_hub import login
from src import config
import json
import re

def load_llm_and_tokenizer():
    """
    Loads the fine-tuned LLM with LoRA parameters and its tokenizer,
    as specified by the model's documentation.
    """
    print("Logging into Hugging Face...")
    login(token=config.HUGGING_FACE_TOKEN)

    print("Loading fine-tuned LLM with LoRA adapter (this may take a while)...")
    
    # Correctly load the fine-tuned model using AutoPeftModelForCausalLM
    model = AutoPeftModelForCausalLM.from_pretrained(
        config.LLM_MODEL_NAME,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        load_in_4bit=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(config.LLM_MODEL_NAME)
    
    print("LLM loaded successfully.")
    return model, tokenizer



def format_instruction(input_details: str, event: str) -> str:
    """
    Creates the prompt for the LLM.
    """
    return f"""You are a personal stylist recommending fashion advice and clothing combinations. Use the self body and style description below, combined with the event described in the context to generate 5 self-contained and complete outfit combinations.
        ### Input:
        {input_details}

        ### Context:
        I'm going to a {event}.

        ### Response:
    """


def parse_outfit_recommendation(text: str) -> list | None:
    """
    Parses the model's markdown list output into a structured list of dictionaries.
    """
    try:
        outfits = []
        # Split the text into chunks for each outfit, using the numbering (1., 2., etc.) as a delimiter
        outfit_chunks = re.split(r'\n\d+\.\s*Outfit:', text)
        
        for chunk in outfit_chunks:
            if not chunk.strip():
                continue
            
            outfit_dict = {}
            # Find all the "- Key: Value" lines
            lines = chunk.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('-'):
                    # Split the line at the first colon
                    parts = line[1:].split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        # Capitalize the key for consistency (e.g., 'top' -> 'Top')
                        outfit_dict[key.capitalize()] = value
            
            if outfit_dict:
                outfits.append(outfit_dict)
                
        if not outfits:
            raise ValueError("No valid outfits could be parsed from the text.")
            
        print(f"Successfully parsed {len(outfits)} outfits.")
        return outfits

    except Exception as e:
        print(f"Error parsing LLM markdown output: {e}")
        return None

def get_outfit_recommendation(details: str, event: str, model, tokenizer) -> list | None:
    """
    Generates outfit recommendations and parses the markdown output.
    """
    prompt = format_instruction(details, event)
    input_ids = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).input_ids.to(model.device)
    
    print("Generating recommendation...")
    with torch.inference_mode():
        outputs = model.generate(
            input_ids=input_ids, max_new_tokens=1024, do_sample=True, top_p=0.9, temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    raw_output = response_text[len(prompt):].strip()

    # --- USE THE NEW REGEX PARSER ---
    return parse_outfit_recommendation(raw_output)