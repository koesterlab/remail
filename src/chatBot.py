import streamlit as st
from llama_cpp import Llama
import chromadb as db
from chromadb.utils import embedding_functions
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Streamlit App Configuration
st.set_page_config(page_title="🦙💬 Llama-cpp Chatbot")

# Llama-cpp Configuration
MODEL_PATH = "./.llama/Llama-3.2-1B-Instruct-f16.gguf"  # Update with your model file path
llama = Llama(model_path=MODEL_PATH, n_ctx=512, n_batch=128)

def generate_llama_response(prompt_input):
    """Generates a response using Llama-cpp"""
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

def setup_vector_database(directory_path="./remail/oz.txt", collection_name="quickstart", embed_model_name="./.llama/pytorch_model.bin"):
    """
    Sets up the Chroma vector database with embedded documents.
    
    Args:
        directory_path (str): Path to the directory or file containing documents.
        collection_name (str): Name of the Chroma collection.
        embed_model_name (str): Name of the HuggingFace embedding model.

    Returns:
        VectorStoreIndex: The initialized vector store index with embedded documents.
    """
    try:
        # Create Chroma client and collection
        chroma_client = db.EphemeralClient()
        chroma_collection = chroma_client.create_collection(collection_name)

        # Define embedding model
        embed_model = HuggingFaceEmbedding(model_name=embed_model_name)

        # Load documents from the specified directory
        documents = SimpleDirectoryReader(directory_path).load_data()

        # Initialize ChromaVectorStore and load data
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create and return the index
        return VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=embed_model
        )
    except Exception as e:
        st.error(f"Error setting up vector database: {e}")
        return None

# Initialize the vector database
index = setup_vector_database()

# Ensure the index is properly loaded
if index is None:
    st.warning("Vector database setup failed. The chatbot might not work as intended.")


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
