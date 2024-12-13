import streamlit as st
from llama_cpp import Llama
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.response_synthesizers import BaseSynthesizer
import chromadb as db

# Streamlit App Configuration
st.set_page_config(page_title="🦙💬 Llama-cpp Chatbot")

# Llama-cpp Configuration
MODEL_PATH = "./.llama/Llama-3.2-1B-Instruct-f16.gguf"  # Update with your model file path
llama = Llama(model_path=MODEL_PATH, n_ctx=8192, n_batch=128)

# Hugging Face Embedding Model
EMBEDDING_MODEL_PATH = "./local-embedding-model"
embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL_PATH)

# Custom Synthesizer Implementation
class SimpleSynthesizer(BaseSynthesizer):
    def _get_prompts(self, query_str, nodes):
        # Generate a prompt from the query and the retrieved documents (nodes)
        prompt = f"Question: {query_str}\n\nDocuments:\n"
        for node in nodes:
            prompt += f"{node.text[:200]}...\n"  # Display a snippet of the document
        prompt += "\nAnswer:"
        return [prompt]

    def _update_prompts(self, prompts, new_text):
        # Update the prompts with new text (if applicable)
        prompts[0] += "\n" + new_text
        return prompts

    async def aget_response(self, prompts):
        # Asynchronous method to generate a response (not used here, but needs to be implemented)
        return self.get_response(prompts)

    def get_response(self, prompts):
        # Generate a response from the LLM based on the prompt
        response = llama(prompts[0], max_tokens=150, temperature=0.7)
        return response["choices"][0]["text"].strip()

# RAG Query Engine (Retriever + Synthesizer)
class RAGQueryEngine(CustomQueryEngine):
    """RAG Query Engine."""

    retriever: BaseRetriever
    response_synthesizer: SimpleSynthesizer

    def custom_query(self, query_str: str):
        # Retrieve relevant documents from the vector store
        nodes = self.retriever.retrieve(query_str)
        # Synthesize a response using the retrieved documents
        response_obj = self.response_synthesizer.synthesize(query_str, nodes)
        return response_obj

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

def setup_vector_database(directory_path="./src/vectorData", collection_name="quickstart"):
    try:
        # Load documents
        documents = SimpleDirectoryReader(directory_path).load_data()
        print("Data loaded!")
        print(f"Number of documents loaded: {len(documents)}")
        for i, doc in enumerate(documents[:5]):  # Print first 5 documents
            print(f"Document {i + 1}: {doc.text[:20]}...")  # Show first 20 characters

        # Initialize ChromaDB client and collection
        chroma_client = db.PersistentClient(path="./db/chroma_db")
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("DB initialized!")

        # Create VectorStoreIndex with LLM explicitly set to None
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context, 
            embed_model=embed_model, 
            llm=None  # Disable OpenAI LLM usage explicitly
        )
        print("VectorStore created!")
        print(f"Chroma collection size: {len(chroma_collection.get()['documents'])}")
        
        return index
    except Exception as e:
        st.error(f"Error setting up vector database: {e}")
        return None


# Initialize the vector database
index = setup_vector_database()

# Ensure the index is properly loaded
if index is None:
    st.warning("Vector database setup failed. The chatbot might not work as intended.")
else:
    # Run a test query after the index is created
    print("idex is loaded")

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
