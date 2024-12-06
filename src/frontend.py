import streamlit as st
from EMailService import ImapProtocol, ExchangeProtocol
from email2 import Email, EmailReception, Contact, RecipientKind, Attachment



# Streamlit-Konfiguration
st.set_page_config(page_title="Remail", layout="wide")

# Globale Variablen für den Status
if 'protocol' not in st.session_state:
    st.session_state['protocol'] = None
if 'emails' not in st.session_state:
    st.session_state['emails'] = []

# Hilfsfunktion zum Laden von E-Mails
def load_emails():
    if st.session_state['protocol']:
        st.session_state['emails'] = st.session_state['protocol'].get_emails()

# Sidebar: Verbindung zu Protokollen
with st.sidebar:
    st.header("Email Service Login")
    protocol_type = st.selectbox("Select Protocol", ["IMAP", "Exchange"])

    user = st.text_input("Email Address")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if protocol_type == "IMAP":
            protocol = ImapProtocol()
        elif protocol_type == "Exchange":
            protocol = ExchangeProtocol()
        
        if protocol.login(user, password):
            st.success("Logged in successfully!")
            st.session_state['protocol'] = protocol
            load_emails()
        else:
            st.error("Login failed. Check your credentials.")

    if st.button("Logout"):
        if st.session_state['protocol']:
            st.session_state['protocol'].logout()
            st.session_state['protocol'] = None
            st.session_state['emails'] = []
            st.success("Logged out successfully!")

# Hauptinhalt: Tabs für verschiedene Aktionen
tabs = st.tabs(["Inbox", "Compose", "Settings"])

# Tab: Inbox
with tabs[0]:
    st.header("Inbox")

    if st.session_state['protocol']:
        emails = st.session_state['emails']

        if emails:
            for email in emails:
                if st.button(f"{email.subject} - {email.sender.email_address}"):
                    st.session_state['selected_email'] = email
        else:
            st.write("No emails available.")

        if 'selected_email' in st.session_state:
            selected_email = st.session_state['selected_email']
            st.subheader(f"Subject: {selected_email.subject}")
            st.write(f"From: {selected_email.sender.email_address}")
            st.write(f"Body: {selected_email.body}")

            if st.button("Delete Email"):
                if st.session_state['protocol'].delete_email(selected_email.id):
                    st.success("Email deleted.")
                    load_emails()
                else:
                    st.error("Failed to delete email.")

# Tab: Compose
with tabs[1]:
    st.header("Compose Email")

    if st.session_state['protocol']:
        to = st.text_input("To")
        cc = st.text_input("CC")
        bcc = st.text_input("BCC")
        subject = st.text_input("Subject")
        body = st.text_area("Body")
        attachment_path = st.file_uploader("Attachment", type=["txt", "pdf", "jpg", "png"])

        if st.button("Send"):
            to_recipients = [EmailReception(contact=Contact(email_address=addr), kind=RecipientKind.to) for addr in to.split(",")]
            cc_recipients = [EmailReception(contact=Contact(email_address=addr), kind=RecipientKind.cc) for addr in cc.split(",")] if cc else []
            bcc_recipients = [EmailReception(contact=Contact(email_address=addr), kind=RecipientKind.bcc) for addr in bcc.split(",")] if bcc else []

            attachments = []
            if attachment_path:
                attachments.append(Attachment(filename=attachment_path.name))

            email = Email(
                subject=subject,
                body=body,
                recipients=to_recipients + cc_recipients + bcc_recipients,
                attachments=attachments
            )

            if st.session_state['protocol'].send_email(email):
                st.success("Email sent successfully!")
            else:
                st.error("Failed to send email.")

# Tab: Settings
with tabs[2]:
    st.header("Settings")
    st.write("Settings functionality coming soon!")
