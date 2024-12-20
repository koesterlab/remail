# from sqlmodel import create_engine
# from controllers.email_controller import EmailController
# from models import SQLModel, Contact

# engine = create_engine("duckdb:///test.db")
# SQLModel.metadata.create_all(engine)

# Controller initialisieren
# email_controller = EmailController(engine)

# Beispiel-Operationen
# Absender und Empfänger erstellen
# with Session(engine) as session:
#    sender = Contact(name="Alice", email_address="alice@example.com")
#    recipient = Contact(name="Bob", email_address="bob@example.com")
#    session.add(sender)
#    session.add(recipient)
#    session.commit()

# Neue E-Mail erstellen
#email_controller.create_email(
#    sender_email="alice@example.com",
#    recipient_emails=["bob@example.com"],
#    subject="Meeting Update",
#    body="Das Meeting wurde auf 15 Uhr verschoben.",
#)

# E-Mails abrufen
#emails = email_controller.get_emails(sender_email="alice@example.com")
#for email in emails:
#    print(f"Betreff: {email.subject}, Body: {email.body}")

# Betreff aktualisieren
#email_controller.update_email_subject(email_id=1, new_subject="Wichtige Info")

# E-Mail löschen
#email_controller.delete_email(email_id=1)
