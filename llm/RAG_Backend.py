import chromadb as db
import hashlib
import os 
from llama_cpp import Llama
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pathlib import Path
from llama_index.core.query_engine import RetrySourceQueryEngine, RetrySourceQueryEngine
from llama_index.core.evaluation import RelevancyEvaluator

class LLM(object):
    def __init__(self):
        MODEL_PATH = "./llm/models/Llama-3.2-1B-Instruct-Q8_0.gguf"  # requires model to be downloaded. replace with huggingface link to change
        EMBEDDING_MODEL_PATH = "BAAI/bge-large-en-v1.5" # replace with huggingface link to change

        # Disable OpenAI usage by explicitly setting LLM to None => Uses integrated MockLLM
        Settings.llm = None
        Settings.context_window = 8192 # arbitrary number, llama 3.2 can do up to 128k

        # Llama-cpp Configuration
        self._llama = Llama(model_path=MODEL_PATH, n_ctx=Settings.context_window, chat_format="llama-3", verbose=False) # disabling verbosity to reduce console logging

        # Hugging Face Embedding Model
        Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_PATH)

        #Directory Configuration
        self._hash_file ="./llm/db/data_hash.txt"
        self._data_folder ="./llm/vectorData"
        self._db_path="./llm/db/chroma_db"
        self._collection_name = "quickstart"


        # Initialize ChromaDB client and collection
        self._chroma_client = db.PersistentClient(path=self._db_path)
        self._chroma_collection = self._chroma_client.get_or_create_collection(self._collection_name)
        self._vector_store = ChromaVectorStore(chroma_collection=self._chroma_collection)
        self._storage_context = StorageContext.from_defaults(vector_store=self._vector_store)
        
        # Check for new documents, and either load the vector db from file or recreate it.
        try:
            self._current_hash = self._compute_folder_hash(self._data_folder)
            previous_hash = None

            # Read the previous hash if it exists
            if Path(self._hash_file).exists():
                with open(self._hash_file, "r") as f:
                    previous_hash = f.read().strip()
            #check differences
            if self._current_hash == previous_hash:
                # If no changes, just load the vector store
                print("No new documents found. Loading existing vector store...")
                index = VectorStoreIndex.from_vector_store( 
                    vector_store=self._vector_store,
                    storage_context=self._storage_context, 
                    embed_model=Settings.embed_model, 
                    llm=None  # to disable requirement for OpenAI API key
                )
            else:
                index = self._setup_index()
        except Exception as e:
            raise e #raising error as there's no point in continuing if the VDB is not available

        # Ensure the index is properly loaded
        if index is None:
            raise Exception("Vector Index not initialized. Vector database setup might've failed.")
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

    def _setup_index(self):
        """initial setup of the Vector Store Index, creating the embedding"""
        try:
            # Load documents
            documents = SimpleDirectoryReader(self._data_folder).load_data()
            print("Data loaded!")        

            # Create VectorStoreIndex with LLM explicitly set to None
            index = VectorStoreIndex.from_documents(
                documents, 
                storage_context=self._storage_context, 
                embed_model=Settings.embed_model, 
                llm=None  # to disable requirement for OpenAI API key
            )
            print("index created!")
            
            # Save the current hash for future runs
            with open(self._hash_file, "w") as f:
                f.write(self._current_hash)
            return index
        except Exception as e:
            raise e

    def _compute_folder_hash(self, folder_path):
        """Compute a hash of all files in the folder to detect changes."""
        hash_obj = hashlib.md5()
        for root, _, files in os.walk(folder_path):
            for file in sorted(files):  # Sort files to ensure consistent ordering
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):  # Read file in chunks
                        hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def prompt(self, prompt: str) -> str:
        """Generates a response"""
        try:
            context = self._query_engine.query(prompt).response
            response = self._llama(context, max_tokens=Settings.context_window)["choices"][0]["text"].strip()
            return response
        except Exception as e:
            return f"An error occurred: {str(e)}"