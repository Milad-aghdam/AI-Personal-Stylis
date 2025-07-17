from src.config import TELEGRAM_API_TOKEN, HUGGING_FACE_TOKEN
from src.llm import load_llm_and_tokenizer
from src.retriever import load_database
from src.bot import run_bot

if __name__ == "__main__":
    # 1. Check if secrets are set
    if not TELEGRAM_API_TOKEN or not HUGGING_FACE_TOKEN:
        print("ERROR: API tokens are not set. Please create a .env file.")
        exit()

    # 2. Load the AI models
    llm_model, tokenizer = load_llm_and_tokenizer()

    # 3. Load the vector database
    db = load_database()

    # 4. Start the bot and pass the loaded components to it
    run_bot(llm_model, tokenizer, db)