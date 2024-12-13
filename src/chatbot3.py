import streamlit as st
import chromadb as db
import hashlib
import os 
from llama_cpp import Llama
from llama_index.core import Settings,VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pathlib import Path
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# Replace 'all-MiniLM-L6-v2' with your desired model name
# model = SentenceTransformer('all-MiniLM-L6-v2')
# model.save('./local-embedding-model')

# Disable OpenAI usage by explicitly setting API key to None
Settings.llm = None
st.set_page_config(page_title="🦙💬 Llama-cpp Chatbot")
# Llama-cpp Configuration
MODEL_PATH = "./.llama/Llama-3.2-1B-Instruct-f16.gguf"  # Update with your model file path
llama = Llama(model_path=MODEL_PATH, n_ctx=8192, n_batch=128)
# Hugging Face Embedding Model
EMBEDDING_MODEL_PATH = "./local-embedding-model"
Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_PATH)
hash_file ="./db/data_hash.txt"
data_folder ="./src/vectorData"
db_path="./db/chroma_db"
collection_name = "quickstart"


def generate_llama_response(prompt_input):
    """Generates a response using Llama-cpp."""
    dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'.\n"
    for message in st.session_state.messages:
        if message["role"] == "user":
            dialogue += "User: " + message["content"] + "\n\n"
        else:
            dialogue += "Assistant: " + message["content"] + "\n\n"
    try:
        response = llama(dialogue + prompt_input + " Assistant:",
                         max_tokens=max_length,
                         temperature=temperature,
                         top_p=top_p)
        return response["choices"][0]["text"].strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

def setup_vector_database(directory_path=data_folder, collection_name="quickstart"):
    try:
        # Load documents
        documents = SimpleDirectoryReader(directory_path).load_data()
        print("Data loaded!")
        print(f"Number of documents loaded: {len(documents)}")
        for i, doc in enumerate(documents[:5]):  # Print first 5 documents
            print(f"Document {i + 1}: {doc.text[:20]}...")  # Show first 20 characters
        
#test

        # some ad hoc document refinement
        print(len(documents))
        for doc in documents:
        # Since some pages may consist of only images
            if len(doc.text) == 0 :
                documents.remove(doc)
                continue

        print(len(documents))
#test

        # Initialize ChromaDB client and collection
        chroma_client = db.PersistentClient(path=db_path)
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("DB initialized!")

        # Create VectorStoreIndex with LLM explicitly set to None
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context, 
            embed_model=Settings.embed_model, 
            llm=None  # Disable OpenAI LLM usage explicitly
        )
        print("VectorStore created!")
        print(f"Chroma collection size: {len(chroma_collection.get()['documents'])}")
        
        # Save the current hash for future runs
        with open(hash_file, "w") as f:
            f.write(current_hash)

        print(f"Chroma collection size: {len(chroma_collection.get()['documents'])}")
        return index
    except Exception as e:
        st.error(f"Error setting up vector database: {e}")
        return None

def compute_folder_hash(folder_path):
    """Compute a hash of all files in the folder to detect changes."""
    hash_obj = hashlib.md5()
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):  # Sort files to ensure consistent ordering
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):  # Read file in chunks
                    hash_obj.update(chunk)
    return hash_obj.hexdigest()

try:
    # Step 1: Check for new documents
    current_hash = compute_folder_hash(data_folder)
    previous_hash = None

    # Read the previous hash if it exists
    if Path(hash_file).exists():
        with open(hash_file, "r") as f:
            previous_hash = f.read().strip()

    if current_hash == previous_hash:
        # If no changes, just load the vector store
        print("No new documents found. Loading existing vector store...")
        chroma_client = db.PersistentClient(path=db_path)
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        print(f"Chroma collection size: {len(chroma_collection.get()['documents'])}")
    else: setup_vector_database
except Exception as e:
    print(f"Error setting up vector database: {e}")

# Initialize the vector database
index = setup_vector_database()

# set number of docs to retreive
top_k = 2

# configure retriever
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=top_k,
)

# assemble query engine
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
)

# Ensure the index is properly loaded
if index is None:
    st.warning("Vector database setup failed. The chatbot might not work as intended.")
else:
    # Run a test query after the index is created
    print("looks good so far")

# Sidebar Configuration
with st.sidebar:
    st.title('🦙💬 Llama-cpp Chatbot')
    st.write('This chatbot is created using the Llama-cpp library.')

    st.subheader('Models and Parameters')
    temperature = st.slider('Temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.slider('Top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.slider('Max Length', min_value=20, max_value=256, value=50, step=5)

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.button('Clear Chat History', on_click=clear_chat_history)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input and Response Generation
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama_response(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
