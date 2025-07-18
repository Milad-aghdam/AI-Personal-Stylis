# build_database.py

import os
import shutil
import pandas as pd
from src import config
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

def build_database():
    """
    Reads the source CSV, creates vector embeddings, and persists them to ChromaDB.
    """
    # 1. Clean up old database if it exists
    if os.path.exists(config.DB_PERSIST_DIRECTORY):
        print("Found old database. Deleting it to rebuild...")
        shutil.rmtree(config.DB_PERSIST_DIRECTORY)

    # 2. Load the source data
    print(f"Loading data from {config.DATA_PATH}...")
    if not os.path.exists(config.DATA_PATH):
        print(f"❌ ERROR: Data file not found at {config.DATA_PATH}.")
        return
    df = pd.read_csv(config.DATA_PATH)

    # 3. Prepare documents and metadata
    print(f"Processing {len(df)} rows...")
    docs, metadatas = [], []
    for index, row in df.iterrows():
        docs.append(f"For {row['gender']} - {row['name']} - {row.get('description', '')}")
        metadatas.append({
            "index_in_db": index,
            "images": str(row.get('images', '')),
            "price": float(row['price']),
            "name": str(row['name']),

        })

    # 4. Create embeddings and persist the database
    print("Creating embeddings and building the database. This may take a few minutes...")
    embedding_function = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    
    db = Chroma.from_texts(
        texts=docs,
        metadatas=metadatas,
        embedding=embedding_function,
        persist_directory=config.DB_PERSIST_DIRECTORY,
    )
    
    print("✅ Database built and saved successfully!")

if __name__ == "__main__":
    build_database()