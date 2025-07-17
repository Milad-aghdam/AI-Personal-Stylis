import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, BitsAndBytesConfig
from huggingface_hub import login
from src import config

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
    Creates the full prompt for the LLM according to the specified format.
    """
    # This is the exact prompt structure from the model card.
    return f"""You are a personal stylist recommending fashion advice and clothing combinations. Use the self body and style description below, combined with the event described in the context to generate 5 self-contained and complete outfit combinations.
        ### Input:
        {input_details}

        ### Context:
        I'm going to a {event}.

        ### Response:
    """

def get_outfit_recommendation(details: str, event: str, model, tokenizer) -> str:
    """
    Generates outfit recommendations using the provided LLM and tokenizer.
    """
    # 1. Format the instruction prompt
    prompt = format_instruction(details, event)
    
    # 2. Tokenize the prompt for the model
    input_ids = tokenizer(prompt, return_tensors="pt", truncation=True).input_ids.to(model.device)
    
    # 3. Perform inference
    print("Generating recommendation...")
    with torch.inference_mode():
        outputs = model.generate(
            input_ids=input_ids, 
            max_new_tokens=800, 
            do_sample=True, 
            top_p=0.9,
            temperature=0.9
        )
    
    # 4. Decode the output and strip the prompt from the beginning
    #    to get only the new, generated text.
    response_text = tokenizer.batch_decode(outputs.detach().cpu().numpy(), skip_special_tokens=True)[0]
    recommendation = response_text[len(prompt):].strip()
    
    print("Recommendation generated.")
    return recommendation