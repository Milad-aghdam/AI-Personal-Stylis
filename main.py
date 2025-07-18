# In main.py
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from src.config import TELEGRAM_API_TOKEN, HUGGING_FACE_TOKEN
from src.llm import load_llm_and_tokenizer
from src.retriever import load_database 
from src.bot import run_bot

if __name__ == "__main__":
    print("🚀 Starting the AI Personal Stylist Bot...")
    if not TELEGRAM_API_TOKEN or not HUGGING_FACE_TOKEN:
        print("❌ ERROR: API tokens not set.")
        exit()
    print("✅ API tokens found.")
    
    llm_model, tokenizer = load_llm_and_tokenizer()
    db = load_database()
    
    # We can remove the inspection call now
    # print("Inspecting the first entry in the database...")
    # inspect_database_entry(db, index=0)
    
    run_bot(llm_model, tokenizer, db)