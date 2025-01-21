from sqlmodel import Session, select, create_engine
from remail.database.models import Email, Contact, EmailReception, RecipientKind, Attachment, User
from datetime import datetime
import duckdb
import logging
from sqlmodel import SQLModel
from remail.database.setup import init_db



class EmailController:
    def __init__(self):
        # Connect to the DuckDB database (will create a file-based database if it doesn't exist)
        init_db() #init_db() aus remail/setup.py

        engine = create_engine("duckdb:///database.db")
        SQLModel.metadata.create_all(engine)
        self.engine = engine

        # logging.basicConfig(level=logging.INFO)
        # logger = logging.getLogger(__name__)
        #
        # logger.info("Datenbank initialisiert")

    def create_user(self, name: str, email: str):
        """Erstellt einen neuen Benutzer und speichert ihn in der Datenbank."""
        with Session(self.engine) as session:
            existing_user = session.exec(select(User).where(User.email == email)).first()
            if existing_user:
                raise ValueError(f"Ein Benutzer mit der E-Mail {email} existiert bereits.")

            user = User(name=name, email=email)
            session.add(user)
            session.commit()
            # self.logger.info(f"Benutzer erstellt: {name} ({email})")

    def create_email(
        self,
        id: int,
        sender_email: str,
        recipient_emails: list,
        subject: str,
        body: str,
        attachments: list = None,
        urgency: int = None,
        date: datetime = None,
    ):
        """Erstellt eine neue E-Mail und speichert sie in der Datenbank."""
        with Session(self.engine) as session:
            sender = session.exec(select(Contact).where(Contact.email_address == sender_email)).first()
            if not sender:
                raise ValueError("Absender nicht gefunden")

            recipients = []
            for recipient_email in recipient_emails:
                contact = session.exec(select(Contact).where(Contact.email_address == recipient_email)).first()
                if not contact:
                    raise ValueError(f"Empfänger {recipient_email} nicht gefunden")
                recipients.append(EmailReception(contact=contact, kind=RecipientKind.to))

            email = Email(
                id=id,
                sender=sender,
                subject=subject,
                body=body,
                attachments=attachments,
                recipients=recipients,
                date=datetime.now(),
                urgency=urgency,
            )

            if attachments:
                email.attachments = [Attachment(filename=filename) for filename in attachments]

            session.add(email)
            session.commit()
            # self.logger.info(f"E-Mail erstellt: {subject} von {sender_email}")

    def get_emails(self, sender_email=None, recipient_email=None):
        """Liest E-Mails basierend auf Absender oder Empfänger aus."""
        with Session(self.engine) as session:
            query = select(Email)
            if sender_email:
                query = query.where(Email.sender.has(email_address=sender_email))
            if recipient_email:
                query = query.where(
                    Email.recipients.any(
                        EmailReception.contact.has(email_address=recipient_email)
                    )
                )
            emails = session.exec(query).all()
            # self.logger.info(f"{len(emails)} E-Mails gefunden.")
            return emails

    def update_email_subject(self, email_id: int, new_subject: str):
        """Aktualisiert den Betreff einer E-Mail."""
        with Session(self.engine) as session:
            email = session.get(Email, email_id)
            if not email:
                raise ValueError("E-Mail nicht gefunden")
            email.subject = new_subject
            session.add(email)
            session.commit()

    def delete_email(self, email_id: int):
        """Löscht eine E-Mail basierend auf ihrer ID."""
        with Session(self.engine) as session:
            email = session.get(Email, email_id)
            if not email:
                raise ValueError("E-Mail nicht gefunden")
            session.delete(email)
            session.commit()
    
    def create_contact(self, email_address: str, name: str = None):
        """Erstellt einen neuen Kontakt und speichert ihn in der Datenbank."""
        try:
            with Session(self.engine) as session:
                existing_contact = session.exec(select(Contact).where(Contact.email_address == email_address)).first()
                if existing_contact:
                    raise ValueError(f"Kontakt mit der E-Mail-Adresse {email_address} existiert bereits.")

                contact = Contact(email_address=email_address, name=name)
                session.add(contact)
                session.commit()
                return contact
        except Exception as e:
            raise RuntimeError(f"Fehler beim Erstellen des Kontakts: {str(e)}") #Runtime Error werfen


    def get_contacts(self):
        """Gibt alle Kontakte aus."""
        with Session(self.engine) as session:
            contacts = session.exec(select(Contact)).all()
            # self.logger.info(f"{len(contacts)} Kontakte gefunden.")
            return contacts


controller = EmailController()


# ret = controller.create_email("yasin.arazay@gmail.com", ["recipient@gmail.com"], "Generic Subject", "HELLLO")
# print(ret)
