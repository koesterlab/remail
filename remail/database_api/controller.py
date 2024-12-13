from sqlmodel import Session, select
from models import Email, Contact, EmailReception, RecipientKind, Attachment
from datetime import datetime


class EmailController:
    def __init__(self, engine):
        self.engine = engine

    def create_email(
        self,
        sender_email: str,
        recipient_emails: list,
        subject: str,
        body: str,
        attachments: list = None,
    ):
        """Erstellt eine neue E-Mail und speichert sie in der Datenbank."""
        with Session(self.engine) as session:
            sender = session.exec(select(Contact).where(Contact.email_address == sender_email)).first()
            if not sender:
                raise ValueError("Absender nicht gefunden")

            recipients = []
            for recipient_email in recipient_emails:
                contact = session.exec(
                    select(Contact).where(Contact.email_address == recipient_email)
                ).first()
                if not contact:
                    raise ValueError(f"Empfänger {recipient_email} nicht gefunden")
                recipients.append(
                    EmailReception(contact=contact, kind=RecipientKind.to)
                )

            email = Email(
                sender=sender,
                subject=subject,
                body=body,
                recipients=recipients,
                date=datetime.now(),
            )

            if attachments:
                for filename in attachments:
                    email.attachments.append(Attachment(filename=filename))

            session.add(email)
            session.commit()

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
            return session.exec(query).all()

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
