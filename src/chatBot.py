import streamlit as st
from llama_cpp import Llama
import os

# Streamlit App Configuration
st.set_page_config(page_title="🦙💬 Llama-cpp Chatbot")

# Llama-cpp Configuration
MODEL_PATH = "./.llama/Llama-3.2-1B-Instruct-f16.gguf"  # Update with your model file path
llama = Llama(model_path=MODEL_PATH, n_ctx=512, n_batch=128)

def generate_llama_response(prompt_input):
    """Generates a response using Llama-cpp"""
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'.\n"
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    try:
        response = llama(string_dialogue + prompt_input + " Assistant:",
                         max_tokens=max_length,
                         temperature=temperature,
                         top_p=top_p)
        return response["choices"][0]["text"].strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

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
