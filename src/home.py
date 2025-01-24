import streamlit as st
import time
import random
import mimetypes  # Für die korrekte Erkennung von MIME-Types
from remail.controller import controller
from remail.database.models import Contact


# Beispiel-Daten
emails_data = {
    "sender1@example.com": [
        {
            "type": "sent",
            "message": "Hello! How are you?",
            "date": "2024-01-01",
            "urgency": 2,
        },
        {
            "type": "received",
            "message": "I'm good, thanks! How about you?",
            "date": "2024-01-02",
            "urgency": 1,
        },
        {
            "type": "sent",
            "message": "Doing great, thanks for asking!",
            "date": "2024-01-03",
            "urgency": 3,
        },
    ],
    "sender2@example.com": [
        {
            "type": "received",
            "message": "Don't forget our meeting tomorrow.",
            "date": "2024-01-01",
            "urgency": 2,
        },
        {
            "type": "sent",
            "message": "Thanks for the reminder! I'll be there.",
            "date": "2024-01-02",
            "urgency": 1,
        },
    ],
    "sender3@example.com": [
        {
            "type": "received",
            "message": "Can you review the attached file?",
            "date": "2024-01-01",
            "urgency": 3,
        },
    ],
}


# Initialisiere Session-States
if "selected_sender" not in st.session_state:
    st.session_state.selected_sender = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "new_message" not in st.session_state:
    st.session_state.new_message = ""
if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []
if "ai_user_message" not in st.session_state:
    st.session_state.ai_user_message = ""
if "contacts" not in st.session_state:
    st.session_state.contacts = {}
if "filter_option" not in st.session_state:
    st.session_state.filter_option = "None"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

# Kontakte beim Laden der Seite abrufen (hier direkt nach der Initialisierung)
if "contacts" not in st.session_state or not st.session_state.contacts:
    try:
        # Lade Kontakte aus der Datenbank
        db_contacts = controller.get_contacts()
        
        # Falls Kontakte aus der Datenbank geladen wurden, speichere sie im Session-Status
        if db_contacts:
            st.session_state.contacts = {contact.email_address: contact.name for contact in db_contacts}
        else:
            st.session_state.contacts = {}  # Leeres Dictionary, falls keine Kontakte vorhanden sind
        
    except Exception as e:
        st.error(f"Fehler beim Abrufen der Kontakte: {str(e)}")




# New Mail
def add_email_form():
    st.subheader("Compose New Email")
    recipient = st.text_input("To:", key="recipient_input")
    # cc = st.text_input("Cc:", key="cc_input")
    # bcc = st.text_input("Bcc:", key="bcc_input")
    subject = st.text_input("Subject:", key="subject_input")
    body = st.text_area("Message:", key="body_input")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Send Email", key="send_email_button"):
            if recipient and subject and body:
                emails_data.setdefault(recipient, []).append(
                    {"type": "sent", "message": body}
                )
                st.success("Email sent successfully!")
                st.session_state["email_sent"] = True
            else:
                st.error("Please fill out all required fields.")
    with col2:
        if st.button("Cancel", key="cancel_email_button"):
            st.session_state["cancel_email"] = True


if "email_sent" in st.session_state and st.session_state.pop(
    "email_sent"
):  
    st.rerun()

if "cancel_email" in st.session_state and st.session_state.pop("cancel_email"):
    st.rerun()


# "New Contact"
def new_contact_form():
    st.subheader("Add new contact")
    contact_name = st.text_input("Name:", key="contact_name_input")
    #contact_surname = st.text_input("Surname:", key="contact_surname_input")
    email_address = st.text_input("E-Mail address:", key="email_address_input")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Create new contact", key="create_contact_button"):
            if contact_name and email_address:
                full_name = f"{contact_name}"
                try:
                    # Speichern des neuen Kontakts in der Datenbank
                    contact = controller.create_contact(email_address=email_address, name=full_name)
                    
                    # Kontakte nach dem Erstellen erneut laden und in Session speichern
                    db_contacts = controller.get_contacts()
                    st.session_state.contacts = {contact.email_address: contact.name for contact in db_contacts}
                    
                    st.success(f"Created contact {full_name} with email {email_address}")
                    st.session_state.selected_sender = None
                    #st.rerun() # Wichtig für die Aktualisierung der Kontaktliste
                except ValueError as e:
                    st.error(str(e))
                except RuntimeError as e:  # Fange Runtime Errors ab
                    st.error(f"An unexpected error has occurred: {e}")
            else:
                st.error("Please fill out all required fields.")
    with col2:
        if st.button("Cancel", key="cancel_contact_button"):
            st.rerun()



def send_message_to_sender(sender, message):
    st.session_state.chat_history.setdefault(sender, []).append(
        {"type": "sent", "message": message}
    )
    st.success("Message sent successfully!")


# Layout
empty_col1, col1, empty_col2, col2, empty_col3, col3, empty_col4 = st.columns([1, 8, 2, 8, 2, 8, 1])


with st.sidebar:
    st.header("Emails")
    with st.expander("Add Email"):
        add_email_form()

    st.header("Contacts")
    with st.expander("New Contact"):
        new_contact_form()
    try:
        # Lade Kontakte aus der Datenbank
        db_contacts = controller.get_contacts()
        
    except Exception as e:
        st.error(f"Error fetching contacts: {str(e)}")

    

with col1:
    st.subheader("Inbox")
    # Such- und Filterkomponenten
    st.session_state.filter_option = st.selectbox(
        "Sort by:", options=["None", "Urgency", "Date"], key="filter_option_selectbox"
    )
    st.session_state.search_query = st.text_input(
        "Search for Sender:", key="search_query_input"
    )

    # Sender sortieren basierend auf Filter
    contacts = list(st.session_state.contacts.items())
    if st.session_state.filter_option == "Urgency":
        contacts = sorted(
            contacts,
            key=lambda contact: random.randint(1, 5),
            reverse=True,
        )
    elif st.session_state.filter_option == "Date":
        contacts = sorted(contacts, key=lambda contact: time.time(), reverse=True)

    search_query = st.session_state.search_query.lower()
    if search_query:
        contacts = [
            contact for contact in contacts
            if search_query in contact[0].lower() or search_query in contact[1].lower()
        ]


    # Kontakte anzeigen
    for email, name in contacts:
        if st.button(name, key=f"contact_button_{email}"):
            st.session_state.selected_sender = email


with col2:
    selected_sender = st.session_state.get("selected_sender")

    if selected_sender:
        st.subheader(f"Chat mit {st.session_state.contacts[selected_sender]}")
        chat_history = st.session_state.chat_history.get(selected_sender, [])

        # Initialisiere den Zeitstempel für die letzte Nachricht, falls noch nicht vorhanden
        if "last_message_time" not in st.session_state:
            st.session_state.last_message_time = {selected_sender: time.time()}
        elif selected_sender not in st.session_state.last_message_time:
            st.session_state.last_message_time[selected_sender] = time.time()

        # Simuliere das Eintreffen neuer Nachrichten
        time_diff = time.time() - st.session_state.last_message_time[selected_sender]
        if time_diff > random.randint(3, 7):  # Zufälliges Intervall zwischen 3 und 7 Sekunden
            new_message = f"Automatische Nachricht um {time.strftime('%H:%M:%S')}"
            chat_history.append({"type": "received", "message": new_message})
            st.session_state.last_message_time[selected_sender] = time.time()

        # Nachrichten anzeigen
        for chat in chat_history:
            sender_display = selected_sender if chat["type"] == "received" else "You"

            # Überprüfe, ob die Nachricht existiert und zeige sie an
            if "message" in chat:
                message_display = f"{sender_display}: {chat['message']}"
                st.markdown(message_display, unsafe_allow_html=True)

            # Überprüfe, ob eine Datei angehängt ist und zeige sie an
            if "file_name" in chat:
                mime_type, _ = mimetypes.guess_type(chat["file_name"])
                mime_type = mime_type or "application/octet-stream"

                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; flex-wrap: wrap; width: 100%; word-wrap: break-word; background-color: green;">
                        <span style="color: white; font-weight: bold;">
                            {sender_display}:
                        </span>
                        
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                st.download_button(
                    label=f"Datei herunterladen: {chat['file_name']}",
                    data=chat["file_content"],
                    file_name=chat["file_name"],
                    mime=mime_type,
                )

        # Nachricht und Datei-Eingabe
        new_message = st.text_area(
            "Nachricht eingeben:",
            value=st.session_state.new_message,
            height=100,
            key=f"new_message_input_chat_{selected_sender}",
        )
        uploaded_file = st.file_uploader(
            "Datei anhängen", key=f"file_uploader_{selected_sender}"
        )

        if st.button(f"Senden an {selected_sender}", key=f"send_message_{selected_sender}"):
            # Sicherstellen, dass entweder eine Nachricht oder eine Datei vorhanden ist
            if new_message.strip() or uploaded_file:
                message_data = {"type": "sent"}

                # Nachricht hinzufügen, falls vorhanden
                if new_message.strip():
                    message_data["message"] = new_message
                    st.session_state.new_message = ""

                # Datei hinzufügen, falls vorhanden
                if uploaded_file:
                    message_data["file_name"] = uploaded_file.name
                    message_data["file_content"] = uploaded_file.getvalue()
                    st.write(f"Datei '{uploaded_file.name}' wurde angehängt.")

                # Chatverlauf aktualisieren
                st.session_state.chat_history.setdefault(selected_sender, []).append(message_data)
                st.rerun()
            else:
                st.error("Bitte gib eine Nachricht ein oder hänge eine Datei an.")
    else:
        st.write("Wähle einen Empfänger aus, um den Chatverlauf anzuzeigen.")


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

    st.write("\n" * 5)

    # Chat with AI
    st.markdown(
        """
            <div style="text-align: center; margin-top:300px">
                <h2>Chat with AI</h2>
            </div>
            """,
        unsafe_allow_html=True,
    )

    ai_user_message = st.text_area(
        "Type your message to AI:",
        value=st.session_state.ai_user_message,
        height=100,
        key="ai_message",
    )

    if st.button("Send", key="send_ai_button"):  # Eindeutiger Key
        if ai_user_message.strip():
            st.session_state.ai_chat_history.append(
                {"sender": "You", "message": ai_user_message}
            )

            ai_reply = f"This is a placeholder AI response to: {ai_user_message}"
            st.session_state.ai_chat_history.append(
                {"sender": "AI", "message": ai_reply}
            )

            st.session_state.ai_user_message = ""
            st.rerun()

    for chat in st.session_state.ai_chat_history:
        if chat["sender"] == "AI":
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f"""
                    <div>
                        <span style="border: 2px solid green; padding: 2px 5px; border-radius: 5px; color: green; font-weight: bold;">AI:</span>
                        <span style="padding-left: 10px;">{chat['message']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            col1, col2 = st.columns([1, 3])
            with col2:
                st.markdown(
                    f"""
                        <div>
                            <span style="border: 2px solid white; padding: 2px 3px; border-radius: 5px; color: white; font-weight: bold;">
                                You:
                            </span> 
                            <span style="padding-left: 15px;">{chat['message']}</span>
                        </div>
                        """,
                    unsafe_allow_html=True,
                )
