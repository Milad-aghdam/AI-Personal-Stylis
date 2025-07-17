import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

# Model and Data Paths
DATA_PATH = "data/raw/Myntra_fashion_products_fixed.csv" 
DB_PERSIST_DIRECTORY = "data/db"

# Hugging Face model identifiers
LLM_MODEL_NAME = "neuralwork/mistral-7b-style-instruct"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"