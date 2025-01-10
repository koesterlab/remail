import streamlit as st
import RAG_Backend as rag

st.set_page_config(page_title="🦙💬 Llama-cpp Chatbot")
llm = rag.LLM()


# Sidebar Configuration
with st.sidebar:
    st.title('🦙💬 Llama-cpp Chatbot')
    st.write('This chatbot is created using the Llama-cpp library.')

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
            response = llm.prompt(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
