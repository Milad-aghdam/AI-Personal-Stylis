# 🤖 AI Personal Stylist Bot

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

An intelligent Telegram bot that acts as a personal fashion advisor. This project leverages a Retrieval-Augmented Generation (RAG) pipeline by integrating a pre-fine-tuned Large Language Model (neuralwork/mistral-7b-style-instruct) with a semantic vector search engine to provide personalized outfit recommendations.



## ✨ Features

*   **👕 Smart Outfit Recommendations:** Generates complete, themed outfits (Top, Bottom, Shoes, Accessories) based on a user's physical attributes, personal style, and the specific event they are attending.
*   **🔍 Semantic Product Search:** Allows users to search a product catalog using natural language descriptions. The search is powered by vector embeddings and uses a **hard metadata filter** to guarantee gender-correct results.
*   **💬 Interactive & Stateful Conversations:** Manages multi-step conversations with users to gather necessary details for recommendations and searches.
*   **🎨 Polished User Interface:** Provides a clean and intuitive user experience with custom keyboards and well-formatted, emoji-enhanced responses.
*   **🐳 Fully Containerized:** The entire application is packaged with Docker, ensuring a consistent and reproducible environment for development and deployment.

---

## 🛠️ Tech Stack & Architecture

This project is built with a modern AI/ML stack, designed for a RAG workflow.

| Category | Technology |
| :--- | :--- |
| **Backend & Bot** | Python 3.11, `py-telegram-bot-api` |
| **AI & ML** | PyTorch, Hugging Face Transformers, PEFT/LoRA |
| **Language Model** | `neuralwork/mistral-7b-style-instruct` (fine-tuned) |
| **Vector Database** | ChromaDB |
| **Embeddings** | `sentence-transformers/all-mpnet-base-v2` |
| **DevOps** | Docker |

---

## 🚀 Getting Started

To run this project locally, you will need **Docker** installed.

### 1. Clone the Repository

```bash
git clone https://github.com/YourUsername/AI-Personal-Stylist.git
cd AI-Personal-Stylist
```
*(Replace `YourUsername` with your actual GitHub username.)*

### 2. Configure Environment Variables

This project uses an `.env` file to manage secret API keys.

1.  **Create your secrets file:** Copy the example template to a new file named `.env`.
    ```bash
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Open the new `.env` file in a text editor and replace the placeholder values with your actual API tokens from **Telegram** and **Hugging Face**.

### 3. Build the Vector Database

This is a **one-time setup step** that processes the product data and creates the vector database.

```bash
python build_database.py
```

### 4. Build and Run the Docker Container

1.  **Build the Docker image:** This command packages the entire application into a container.
    ```bash
    docker build -t ai-personal-stylist .
    ```
2.  **Run the container:** This command starts the bot and securely injects your secrets from the `.env` file.
    ```bash
    docker run --rm -it --env-file .env ai-personal-stylist
    ```

Your bot is now running! Open Telegram and start a conversation with it.

---

## 📂 Project Structure

The project is organized into a modular structure for maintainability:

```
.
├── 📄 .env        # Template for environment variables
├── 🐳 Dockerfile            # Blueprint for building the Docker container
├── 📖 README.md             # This file
├── 📜 build_database.py     # Script to build the vector DB (run once)
├── 🚀 main.py               # Main entry point to run the application
├── 📦 requirements.txt      # Pinned Python dependencies
└── 📂 src/                  # Main source code directory
    ├── 🤖 bot.py            # All Telegram bot handlers and logic
    ├── ⚙️ config.py        # Configuration and secret key loading
    ├── 🧠 llm.py            # LLM loading and response generation
    └── 🔍 retriever.py      # Vector DB loading and product search logic
```
