import json
import chromadb as db
import hashlib
import os, sys


# Add the Remail directory (parent folder) to sys.path
remail_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(remail_path)


import requests
from llama_cpp import Llama
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pathlib import Path
from llama_index.core.query_engine import RetrySourceQueryEngine
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.core.schema import Document
import controller

class LLM(object):
    # for installing the model can be changed to any model later
    TARGET_DIR = "./remail/llm/models"
    MODEL_FILE = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
    MODEL_URL = (
        "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/"
        + MODEL_FILE
    )
    MODEL_PATH = "./remail/llm/models/" + MODEL_FILE
    EMBEDDING_MODEL_PATH = "BAAI/bge-large-en-v1.5"

    # Directory Configuration
    _hash_file = "./remail/llm/db/data_hash.txt"
    _data_folder = "./remail/llm/vectorData"
    _db_path = "./remail/llm/db/chroma_db"
    _collection_name = "quickstart"

    def __init__(self):
        # Look up if a llm already exists
        destination_path = os.path.join(self.TARGET_DIR, self.MODEL_FILE)
        if not os.path.exists(destination_path):
            self._llm_installer()

        # Disable OpenAI usage by explicitly! Never remove this
        Settings.llm = None
        Settings.context_window = 8192  # arbitrary number, llama 3.2 can do up to 128k
        Settings.chunk_size=4096
        # Llama-cpp Configuration
        self._llama = Llama(
            model_path=self.MODEL_PATH,
            n_ctx=Settings.context_window,
            chat_format="llama-3",
            verbose=False,
        )  # disabling verbosity to reduce console logging

        # Hugging Face Embedding Model
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=self.EMBEDDING_MODEL_PATH
        )

        # Initialize ChromaDB client and collection
        self._chroma_client = db.PersistentClient(path=self._db_path)
        self._chroma_collection = self._chroma_client.get_or_create_collection(
            self._collection_name
        )
        self._vector_store = ChromaVectorStore(
            chroma_collection=self._chroma_collection
        )
        self._storage_context = StorageContext.from_defaults(
            vector_store=self._vector_store
        )

        # Check for new documents, and either load the vector db from file or recreate it.
        try:
            self._current_hash = self._compute_data_hash()
            previous_hash = None

            # Read the previous hash if it exists
            if Path(self._hash_file).exists():
                with open(self._hash_file, "r") as f:
                    previous_hash = f.read().strip()
            # check differences
            if self._current_hash == previous_hash:
                # If no changes, just load the vector store
                print("No new documents found. Loading existing vector store...")
                index = VectorStoreIndex.from_vector_store(
                    vector_store=self._vector_store,
                    storage_context=self._storage_context,
                    embed_model=Settings.embed_model,
                )
            else:
                index = self._setup_index()
        except Exception as e:
            raise e  # raising error as there's no point in continuing if the VDB is not available

        # Ensure the index is properly loaded
        if index is None:
            raise Exception(  # your mom
                "Vector Index not initialized. Vector database setup might've failed."
            )
        # and raise an exception if it isnt
        else:
            print("Index created!")

        # assemble query engine
        base_query_engine = index.as_query_engine(similarity_top_k=3)
        # use max top_k=<3, otherwise retrieval time will rise unbearably
        # might want to decrease this even further for lower end systems
        # default seems to be 2
        query_response_evaluator = RelevancyEvaluator()
        self._query_engine = RetrySourceQueryEngine(
            base_query_engine, query_response_evaluator, max_retries=2
        )

    def _compute_data_hash(self):
        """Compute a hash of all documents' content and metadata to detect changes."""
        hash_obj = hashlib.sha256()
        
        # Loop through each document in docstore (or whichever data you use)
        for doc in self._db_to_nodes():  # Ensure this method returns the actual documents
            # Concatenate document text and metadata (subject, sender, etc.)
            doc_str = doc.text + json.dumps(doc.metadata, sort_keys=True)  # Sorting metadata for consistent hashing
            hash_obj.update(doc_str.encode('utf-8'))
        
        return hash_obj.hexdigest()

    def _setup_index(self):
        """initial setup of the Vector Store Index, creating the embedding"""
        try:
            # Load documents
            documents = self._db_to_nodes()
            print("Data loaded from Database!")

            # Create VectorStoreIndex
            index = VectorStoreIndex.from_documents(
                documents,
                storage_context=self._storage_context,
                embed_model=Settings.embed_model,
            )
            print("index created!")

            # Save the current hash for future runs
            with open(self._hash_file, "w") as f:
                f.write(self._current_hash)
            return index
            
        except Exception as e:
            raise e

    # def _compute_folder_hash(self, folder_path):
    #     """Compute a hash of all files in the folder to detect changes."""
    #     hash_obj = hashlib.sha256()
    #     for root, _, files in os.walk(folder_path):
    #         for file in sorted(files):  # Sort files to ensure consistent ordering
    #             file_path = os.path.join(root, file)
    #             try:
    #                 with open(file_path, "rb") as f:
    #                     while chunk := f.read(8192):  # Read file in chunks
    #                         hash_obj.update(chunk)
    #             except IOError as e:
    #                 print(f"Warning: Could not read file {file_path}: {str(e)}")
    #                 continue
    #     return hash_obj.hexdigest()

        # Folder exists?
    def _ensure_directory_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _download_file(self, url, destination):
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(destination, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        else:
            raise Exception(f"Failed to download file: HTTP {response.status_code}")

    def _llm_installer(self):
        # Ensure the target directory exists
        self._ensure_directory_exists(self.TARGET_DIR)
        destination_path = os.path.join(self.TARGET_DIR, self.MODEL_FILE)

        # Download the model file
        print(f"[INFO] Downloading {self.MODEL_FILE} to {destination_path}...")
        try:
            self._download_file(self.MODEL_URL, destination_path)
            print(f"[INFO] Model file installed successfully at {destination_path}.")
        except Exception as e:
            print(f"[ERROR] Failed to download the file: {e}")

    def _db_to_nodes(self):
        emails = controller.controller.get_emails()
        docstore = []

        for mail in emails:
            # Use get_full_email_data to retrieve all email-related data
            email_data = controller.controller.get_full_email_data(mail)

            # Define document using the data retrieved
            doc = Document(
                text=email_data["body"],
                metadata={
                    "id": email_data["id"],
                    "message_id": email_data["message_id"],
                    "subject": email_data["subject"],
                    "body": email_data["body"],
                    "time": email_data["date"],
                    "urgency": email_data["urgency"],
                    "sender": email_data["sender"],
                    "recipients": email_data["recipients"]
                }
            )
            # Only to see what gets hashed (for testing)
            f = open("MemStorage.txt", "a")
            f.write(json.dumps({"text": doc.text, "metadata": doc.metadata}) + "\n")            
            f.close()
            docstore.append(doc)
        return docstore
  

    def prompt(self, prompt: str) -> str:
        """Use this for prompting. Takes a string as the input and returns the response as a string"""
        try:
            context = self._query_engine.query(prompt).response
            response = self._llama(context, max_tokens=Settings.context_window)[
                "choices"
            ][0]["text"].strip()
            return response
        except Exception as e:
            return f"An error occurred: {str(e)}"