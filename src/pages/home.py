import streamlit as st
import gettext
_ = gettext.gettext
ngettext = gettext.ngettext


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

    if st.button("Add Email"):
        st.session_state.show_add_email_form = True
    if st.button("New Contact"):
        st.session_state.show_new_contact_form = True


# "Add Email" form
def add_email_form():
    st.subheader("Compose New Email")
    recipient = st.text_input("To:")
    cc = st.text_input("Cc:")
    bcc = st.text_input("Bcc:")
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
                st.error("Please fill out all required fields.")
    with col2:
        if st.button("Cancel"):
            st.session_state.show_add_email_form = False

# "New Contact" form
def new_contact_form():
    st.subheader("Add new contact")
    contactName = st.text_input("Name:")
    emailAdress = st.text_input("E-Mail adress:")
    

    col01, col02 = st.columns(2)
    with col01:
        if st.button("Create new contact"):
            st.success("Created contact")

    with col02:
        if st.button("Cancel"):
            st.session_state.show_new_contact_form = False

empty_col1, col1, empty_col2, col2, empty_col3, col3, empty_col4 = st.columns([0.5, 1, 1, 2, 1, 3, 0.5])

# Main Content
if st.session_state.get("show_add_email_form", False):
    add_email_form()
elif st.session_state.get("show_new_contact_form", False):
    new_contact_form()
else:
    
    # Left column: List senders
    with col1:
        st.subheader("Inbox")
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

    # Initialisiere die Chatnachrichten (falls noch nicht vorhanden)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Initialize the chat messages (if not already present)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Initialize the text for the text field (if not already present)
    if "user_message" not in st.session_state:
        st.session_state.user_message = ""

    with col3:
        # Graph 
        st.markdown(
            """
            <div style="text-align: center;">
                <h2>Graph View</h2>
                <p>This is where the graph could be displayed.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        
        st.write("\n" * 5)  # Spacing

        # Chat with AI
        st.markdown(
            """
            <div style="text-align: center; margin-top:300px">
                <h2>Chat with AI</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Input field for message
        user_message = st.text_area("Type your message to AI:", value=st.session_state.user_message, height=100, key="ai_message")

        #Send button
        if st.button("Send", key="send_ai"):
            if user_message.strip():  # If the message is not empty
                st.session_state.chat_history.append({"sender": "You", "message": user_message})

                ai_reply = f" "  #  insert an actual AI reply
                st.session_state.chat_history.append({"sender": "AI", "message": ai_reply})

                st.session_state.user_message = ""  # The value of the text field should be reset here //// Klappt nicht!!!!

        # Display the entire chat history
        for chat in st.session_state.chat_history:
            if chat["sender"] == "AI":
                # Display the user's message on the left
                col1, col2 = st.columns([3, 1])  
                with col1:
                    st.markdown(
                        f"""
                        <div>
                            <span style="border: 2px solid green; padding: 2px 5px; border-radius: 5px; color: green; font-weight: bold;">
                                AI:
                            </span> 
                            <span style="padding-left: 10px;">{chat['message']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:
                # Display the AI's message on the right
                col1, col2 = st.columns([1, 3])  
                with col2:
                    st.markdown(
                        f"""
                        <div>
                            <span style="border: 2px solid white; padding: 2px 3px; border-radius: 5px; color: white; font-weight: bold;">
                                You:
                            </span> 
                            <span style="padding-left: 10px;">{chat['message']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

