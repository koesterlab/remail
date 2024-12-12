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

# Setting page layout - must be the first command
st.set_page_config(page_title="Remail", layout="wide")

# Sidebar (Left side)
with st.sidebar:
    st.header("Emails")
    email_sections = ["Inbox", "Drafts", "Sent Items", "Deleted Items", "Junk Mail", "Archive"]
    selected_section = st.radio("Sections", email_sections)

    if st.button("Add Email"):
        st.session_state.show_add_email_form = True

# "Add Email" form
def add_email_form():
    st.subheader("Compose New Email")
    recipient = st.text_input("To:")
    subject = st.text_input("Subject:")
    body = st.text_area("Message:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Send Email"):
            if recipient and subject and body:
                if recipient not in emails_data:
                    emails_data[recipient] = []
                emails_data[recipient].append({"type": "sent", "message": body})
                st.success("Email sent successfully!")
                st.session_state.show_add_email_form = False
            else:
                st.error("Please fill out all fields.")
    with col2:
        if st.button("Cancel"):
            st.session_state.show_add_email_form = False
            

# Main Content based on selected section
if st.session_state.get("show_add_email_form", False):
    add_email_form()
else:
    if selected_section == "Inbox":
        col1, col2 = st.columns([1, 2])

        # Left column: List senders
        with col1:
            st.subheader("Emails Sorted by Sender")
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

    elif selected_section == "Drafts":
        st.subheader("Drafts")
        st.write("Here you can view and manage your drafts.")

    elif selected_section == "Sent Items":
        st.subheader("Sent Items")
        st.write("Here are the emails you've sent.")

    elif selected_section == "Deleted Items":
        st.subheader("Deleted Items")
        st.write("Here are your deleted emails.")

    elif selected_section == "Junk Mail":
        st.subheader("Junk Mail")
        st.write("This is your junk mail folder.")

    elif selected_section == "Archive":
        st.subheader("Archive")
        st.write("This is your email archive.")
