import pandas as pd
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from src import config # Use . for relative import
from PIL import Image
import requests
from io import BytesIO

# --- Image helper functions from your notebook ---
# def get_image_by_url(...)
# def concat_images_h(...)
# def concat_images_v(...)

def load_database():
    """Loads or creates the ChromaDB vector database."""
    # This logic should be expanded to check if the DB exists and create it if not
    print("Loading vector database...")
    embedding = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    vectordb = Chroma(persist_directory=config.DB_PERSIST_DIRECTORY, embedding_function=embedding)
    return vectordb

def search_for_products(prompt: str, db: Chroma):
    """
    Takes a user prompt and a database instance, returns image and text.
    """
    # Your retrieval_products logic goes here, adapted to be a function.
    print(f"Searching for: {prompt}")
    documents = db.similarity_search(prompt, k=3)

    if not documents:
        return None, None
    
    # ... The rest of your retrieval_products logic to create the image and text ...
    # For now, let's just return the found documents for simplicity
    final_txt = "Found Products:\n\n"
    for doc in documents:
        final_txt += f"- {doc.metadata['name']} (Price: {doc.metadata['price']})\n"

    # Placeholder for image generation
    final_img = Image.new('RGB', (100, 100), color = 'red') 

    return final_img, final_txt