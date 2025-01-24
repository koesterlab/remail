from sqlmodel import Session, select, create_engine
from remail.database.models import (
    Email,
    Contact,
    EmailReception,
    RecipientKind,
    Attachment,
    User,
    Protocol,
)
from datetime import datetime
import duckdb
import logging
from sqlmodel import SQLModel
from remail.email_api.service import ImapProtocol, ExchangeProtocol, ProtocolTemplate
import remail.email_api.email_errors as errors
import keyring
from tzlocal import get_localzone


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except errors.InvalidLoginData:
            logging.error(
                "Fehler beim Aktualisieren der E-Mails: Ungültige Anmeldedaten"
            )
        except errors.ServerConnectionFail:
            logging.error(
                "Fehler beim Aktualisieren der E-Mails: Serververbindung fehlgeschlagen"
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Fehler beim Aktualisieren der E-Mails")

    return wrapper


class EmailController:
    def __init__(self):
        # Connect to the DuckDB database (will create a file-based database if it doesn't exist)
        conn = duckdb.connect("database.db")
        conn.close()

        engine = create_engine("duckdb:///database.db")
        SQLModel.metadata.create_all(engine)
        self.engine = engine

        self.refresh()  # kann etwas dauern


    def has_user(self):
        with Session(self.engine) as session:        
            return session.exec(select(User).limit(1)).first() is not None

    @error_handler
    def refresh(self):
        """Aktualisiert alle E-Mails in der Datenbank."""
        with Session(self.engine) as session:
            users = session.exec(select(User)).all()
            accounts = []
            for user in users:
                password = keyring.get_password("remail/Account", user.email)

                if user.protocol == Protocol.IMAP:
                    accounts += [
                        (
                            ImapProtocol(
                                email=user.email,
                                host=user.extra_information,
                                password=password,
                                controller=self,
                            ),
                            user.last_refresh,
                            user.email,
                        )
                    ]
                elif user.protocol == Protocol.EXCHANGE:
                    accounts += [
                        (
                            ExchangeProtocol(
                                email=user.email,
                                username=user.extra_information,
                                password=password,
                                controller=self,
                            ),
                            user.last_refresh,
                            user.email,
                        )
                    ]

            self._refresh(accounts)
            for user in users:
                self._update_user_last_refresh(user.email)

    def change_password(self, email: str, password: str):
        """Ändert das Passwort eines Benutzers"""
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.email == email)).first()
            if not user:
                raise ValueError(f"Benutzer mit der E-Mail {email} nicht gefunden.")
            keyring.set_password("remail/Account", email, password)

    def create_user(
        self,
        name: str,
        email: str,
        protocol: Protocol,
        extra_information: str,
        password: str,
    ):
        """Erstellt einen neuen Benutzer und speichert ihn in der Datenbank. extra_information ist username (Exchange) oder host (IMAP)"""
        with Session(self.engine) as session:
            existing_user = session.exec(
                select(User).where(User.email == email)
            ).first()
            if existing_user:
                raise ValueError(
                    f"Ein Benutzer mit der E-Mail {email} existiert bereits."
                )

            user = User(
                name=name,
                email=email,
                protocol=protocol,
                extra_information=extra_information,
            )
            session.add(user)
            session.commit()
            keyring.set_password("remail/Account", email, password)
            # self.logger.info(f"Benutzer erstellt: {name} ({email})")

    def _update_user_last_refresh(self, email: str):
        """updates the date time of the last refresh to the current time"""
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.email == email)).first()
            user.last_refresh = datetime.now(tz=get_localzone())
            session.commit()
            session.refresh(user)

    @error_handler
    def send_email(
        self,
        id: int,
        sender_email: str,
        recipient_emails_to: list,
        recipient_emails_cc: list,
        recipient_emails_bcc: list,
        subject: str,
        body: str,
        attachments: list = None,
        urgency: int = None,
        date: datetime = None,
    ):
        """Erstellt eine neue E-Mail und speichert sie in der Datenbank."""
        with Session(self.engine) as session:
            sender = session.exec(
                select(Contact).where(Contact.email_address == sender_email)
            ).first()
            if not sender:
                raise ValueError("Absender nicht gefunden")

            recipients = []
            for recipient_email in recipient_emails_to:
                contact = session.exec(
                    select(Contact).where(Contact.email_address == recipient_email)
                ).first()
                if not contact:
                    raise ValueError(f"Empfänger {recipient_email} nicht gefunden")
                recipients.append(
                    EmailReception(contact=contact, kind=RecipientKind.to)
                )

            for recipient_email in recipient_emails_cc:
                contact = session.exec(
                    select(Contact).where(Contact.email_address == recipient_email)
                ).first()
                if not contact:
                    raise ValueError(f"Empfänger {recipient_email} nicht gefunden")
                recipients.append(
                    EmailReception(contact=contact, kind=RecipientKind.cc)
                )

            for recipient_email in recipient_emails_bcc:
                contact = session.exec(
                    select(Contact).where(Contact.email_address == recipient_email)
                ).first()
                if not contact:
                    raise ValueError(f"Empfänger {recipient_email} nicht gefunden")
                recipients.append(
                    EmailReception(contact=contact, kind=RecipientKind.bcc)
                )

            email = Email(
                id=id,
                sender=sender,
                subject=subject,
                body=body,
                attachments=attachments,
                recipients=recipients,
                date=datetime.now(tz=get_localzone())
                if date is None
                else date.astimezone(get_localzone()),
                urgency=urgency,
            )

            with Session(self.engine) as session:
                user = session.exec(
                    select(User).where(User.email == sender_email)
                ).first()
                password = keyring.get_password("remail/Account", user.email)
                if user.protocol == Protocol.IMAP:
                    protocol = ImapProtocol(
                        email=user.email, host=user.extra_information, password=password
                    )
                elif user.protocol == Protocol.EXCHANGE:
                    protocol = ExchangeProtocol(
                        email=user.email,
                        username=user.extra_information,
                        password=password,
                        controller=self,
                    )

                protocol.login()
                protocol.send_email(email)
                protocol.logout()

            if attachments:
                email.attachments = [
                    Attachment(filename=filename) for filename in attachments
                ]

            session.add(email)
            session.commit()

    def safe_email(self, list_of_mails: list[Email]):
        """Speichert die E-Mail Objekte aus dem Email_Api Modul"""
        with Session(self.engine) as session:
            for mail in list_of_mails:
                session.merge(mail)
                session.commit()

    def _refresh(self, list_of_protocols: list[ProtocolTemplate, datetime, str]):
        all_mails_database = []
        all_message_ids = []
        all_new_mails = []
        deleted_mails_id = []

        for protocol, date, email_address_acc in list_of_protocols:
            protocol.login()
            with Session(self.engine) as session:
                all_mails_database += self.get_emails(sender_email=email_address_acc)
                all_mails_database += self.get_emails(recipient_email=email_address_acc)
                all_message_ids = [mail.message_id for mail in all_mails_database]

            all_new_mails += protocol.get_emails(date)
            deleted_mails = set(protocol.get_deleted_emails(all_message_ids))
            with Session(self.engine) as session:
                statement_1 = select(Email.id).where(
                    (Email.sender.has(email_address=email_address_acc))
                    & (Email.message_id.in_(deleted_mails))
                )
                statement_2 = (
                    select(EmailReception.email_id)
                    .join(Contact, Contact.id == EmailReception.contact_id)
                    .join(Email, EmailReception.email_id == Email.id)
                    .where(
                        (Contact.email_address == email_address_acc)
                        & (Email.message_id.in_(deleted_mails))
                    )
                )
                deleted_mails_id += session.exec(statement_1).all()
                deleted_mails_id += session.exec(statement_2).all()
            protocol.logout()
        for id in deleted_mails_id:
            self.delete_email(id)

        with Session(self.engine) as session:
            self.safe_email(all_new_mails)

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

            recs = email.recipients
            for rec in recs:
                session.delete(rec)

            atts = email.attachments
            for att in atts:
                session.delete(att)
            session.commit()

        with Session(self.engine) as session:
            email = session.get(Email, email_id)
            if not email:
                raise ValueError("E-Mail nicht gefunden")

            session.delete(email)
            session.commit()

    def create_contact(self, email_address: str, name: str = None):
        """Erstellt einen neuen Kontakt."""
        try:
            with Session(self.engine) as session:
                existing_contact = session.exec(
                    select(Contact).where(Contact.email_address == email_address)
                ).first()
                if existing_contact:
                    raise ValueError(
                        f"Kontakt mit E-Mail {email_address} existiert bereits."
                    )

                contact = Contact(email_address=email_address, name=name)
                session.add(contact)
                session.commit()
                return contact
        except Exception as e:
            raise e

    def change_name_Contact(self, email_address: str, name: str):
        """Change the name of a Contact with a specific email_address"""
        with Session(self.engine) as session:
            contact = session.exec(
                select(Contact).where(Contact.email_address == email_address)
            ).first()
            if not contact:
                raise ValueError(
                        f"Kontakt mit E-Mail {email_address} existiert nicht."
                    )
            contact.name = name
            session.commit()
            session.refresh(contact)

    def get_contacts(self):
        """Gibt alle Kontakte aus."""
        with Session(self.engine) as session:
            contacts = session.exec(select(Contact)).all()
            # self.logger.info(f"{len(contacts)} Kontakte gefunden.")
            return contacts

    def get_contact(self, email: str, name: str = None) -> Contact:
        """Gibt den Kontakt mit der Emailadresse zurück oder erstellt einen neuen"""
        contacts = self.get_contacts()
        contact = [con for con in contacts if con.email_address == email]
        if len(contact) > 0:
            return contact[0]
        else:
            return self.create_contact(email, name)


controller = EmailController()

