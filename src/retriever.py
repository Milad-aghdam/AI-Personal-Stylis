import os
import pandas as pd
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from src import config
from PIL import Image
import requests
from io import BytesIO

# (The image helper functions like get_image_by_url, etc., remain the same. No changes needed there.)
# --- Image helper functions from your notebook ---
def get_image_by_url(url: str) -> Image.Image:
    """Downloads an image from a URL and returns a PIL Image object."""
    response = requests.get(url)
    response.raise_for_status()  
    img = Image.open(BytesIO(response.content))
    return img

def concat_images_h(images: list[Image.Image]) -> Image.Image:
    """Concatenates a list of PIL Images horizontally."""
    if not images:
        return None
    
    width, height = images[0].size
    total_width = width * len(images)
    new_im = Image.new('RGB', (total_width, height))
    
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]
        
    return new_im


def concat_images_v(images: list[Image.Image]) -> Image.Image:
    """Concatenates a list of PIL Images vertically."""
    if not images:
        return None

    width, height = images[0].size
    total_height = height * len(images)
    new_im = Image.new('RGB', (width, total_height))
    
    y_offset = 0
    for im in images:
        new_im.paste(im, (0, y_offset))
        y_offset += im.size[1]
        
    return new_im


def _build_and_persist_db(embedding_function):
    """Private helper to build the DB from scratch."""
    print("Database not found. Creating and persisting a new one...")
    
    if not os.path.exists(config.DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {config.DATA_PATH}. Please upload it.")

    df = pd.read_csv(config.DATA_PATH)
    
    print(f"Processing {len(df)} rows from the dataset...")
    docs, m_data = [], []
    for index, row in df.iterrows():
        # Ensure all data is a string to prevent errors
        docs.append(f"For {row['gender']} - {row['name']} - {row.get('description', '')}")
        m_data.append({
            "index_in_db": index,
            "images": str(row.get('images', '')),
            "price": float(row['price']), # Ensure price is a number
            "name": str(row['name'])
        })

    db = Chroma.from_texts(
        texts=docs,
        metadatas=m_data,
        embedding=embedding_function,
        persist_directory=config.DB_PERSIST_DIRECTORY,
    )
    print("Database created and saved successfully.")
    return db

# In src/retriever.py

def load_database():
    """
    Loads the ChromaDB vector database from disk. Assumes it has already been built.
    """
    if not os.path.exists(config.DB_PERSIST_DIRECTORY):
        raise FileNotFoundError(
            f"Database not found at {config.DB_PERSIST_DIRECTORY}. "
            "Please run 'python build_database.py' first to create it."
        )
    
    print("Loading existing vector database from disk...")
    embedding_function = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    db = Chroma(
        persist_directory=config.DB_PERSIST_DIRECTORY, 
        embedding_function=embedding_function
    )
    print("Database is ready.")
    return db



def search_for_products(prompt: str, gender_filter: str, db: Chroma):
    """
    Takes a user prompt and a database instance, searches for relevant products,
    and returns a composite image and a formatted text description.
    """
    print(f"Searching for '{prompt}' with gender filter: '{gender_filter}'")
    documents = db.similarity_search(prompt,
                                    k=3,
                                    filter={"gender": gender_filter})

    if not documents:
        print("No relevant documents found.")
        return None, None

    tmp_imgs_v = []
    tmp_imgs_info = []

    for cnt, doc in enumerate(documents):
        metadata = doc.metadata
        images_urls = metadata.get("images", "").split("~")
        
        tmp_imgs_h = []
        num_valid_img = 0

        for url in images_urls:
            url = url.strip()
            if not url:
                continue
            
            try:
                img = get_image_by_url(url)
                img = img.resize((256, 256))
                tmp_imgs_h.append(img)
                num_valid_img += 1
                if num_valid_img >= 3:
                    break
            except Exception as e:
                print(f"Warning: Could not fetch image from {url}. Error: {e}")

        if tmp_imgs_h:
            h_concat_img = concat_images_h(tmp_imgs_h)
            tmp_imgs_v.append(h_concat_img)

        info = (
            f"ردیف {cnt + 1}:\n"
            f"قیمت: {metadata.get('price', 'N/A')}\n"
            f"نام محصول: {metadata.get('name', 'N/A')}\n"
            f"شناسه: {metadata.get('index_in_db', 'N/A')}\n"
            "------------------------"
        )
        tmp_imgs_info.append(info)

    # Concatenate the row images vertically
    final_img = concat_images_v(tmp_imgs_v) if tmp_imgs_v else None

    # Prepare final text
    final_txt = "محصولات پیشنهادی ما برای این سؤال است:\n\n"
    final_txt += "\n".join(tmp_imgs_info)
    
    return final_img, final_txt