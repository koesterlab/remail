import streamlit as st
import gettext
_=gettext.gettext
ngettext=gettext.ngettext

# Put _() around all strings that should be translated later on
# ngettext changes everything that is in plural. example ngettext("{0} unread msg","{0} unread msges", "int for the counter")
# Example data

emails_data = {
    "sender1@example.com": [
        {"type": "sent", "message": "Hello! How are you?"},
        {"type": "received", "message": "I'm good, thanks! How about you?"},
        {"type": "sent", "message": "Doing great, thanks for asking!"},
    ],

    "sender2@example.com": [
        {"type": "received", "message": "Don't forget our meeting tomorrow."},
        {"type": "sent", "message": "Thanks for the reminder! I'll be there."},
    ],
    "sender3@example.com": [
        {"type": "received", "message": "Can you review the attached file?"},
    ],
}

# Setting page layout
st.set_page_config(page_title="Remail", layout="wide")

# Sidebar (Left side)
with st.sidebar:
    st.header("Emails")
    email_sections = ["Inbox", "Drafts", "Sent Items", "Deleted Items", "Junk Mail", "Archive"]
    selected_section = st.radio("Sections", email_sections)
    st.button("Add Email")

# Main Content
col1, col2 = st.columns([1, 2])

# Left column: List senders
with col1:
    st.subheader(f"Emails Sorted by Sender")
    selected_sender = None
    for sender in emails_data.keys():
        if st.button(sender):
            st.session_state.selected_sender = sender

# Right column: Chat window
with col2:
    selected_sender = st.session_state.get("selected_sender", None)

    if selected_sender:
        st.subheader(f"Chat with {selected_sender}")
        chat_history = emails_data.get(selected_sender, [])

        # Display chat messages
        for chat in chat_history:
            if chat["type"] == "received":
                st.markdown(f"**{selected_sender}:** {chat['message']}")
            else:
                st.markdown(f"**You:** {chat['message']}")
        
        # Input for new chat messages
        new_message = st.text_input("Type your message:")
        if st.button("Send"):
            emails_data[selected_sender].append({"type": "sent", "message": new_message})
            st.success("Message sent!")

    else:
        st.subheader("Select a sender to view chat history.")


