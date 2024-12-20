from remail.database_api.models import Email, EmailReception, Contact, RecipientKind
from remail.email_api.service import ImapProtocol, ExchangeProtocol
import remail.email_api.credentials_helper as ch
from contextlib import contextmanager
from datetime import datetime
from email.utils import format_datetime
from email.message import EmailMessage

imap_test_email = Email(
    subject="test_imap_mail",
    body="Test!!",
    recipients=[
        EmailReception(
            contact=(Contact(email_address="praxisprojekt-remail@uni-due.de")),
            kind=RecipientKind.to,
        )
    ],
)

exchange_test_email = Email(
    subject="test_exchange_mail",
    body="Test!!",
    recipients=[
        EmailReception(
            contact=(Contact(email_address="thatchmilo35@gmail.com")),
            kind=RecipientKind.to,
        )
    ],
)

email_message = EmailMessage()
email_message["Message-Id"] = "test-id"
email_message["From"] = "test@example.com"
email_message["Subject"] = "Test Subject"
email_message["To"] = "recipient@example.com"
email_message["Cc"] = None
email_message["Bcc"] = None
email_message["Date"] = format_datetime(datetime(2024, 1, 1, 12, 0, 0))
email_message.set_content("This is a test email body.")
# email_message.add_attachment(b"Test content", filename="test.txt")


@contextmanager
def email_test_context():
    ch.protocol = ch.Protocol.IMAP
    imap = ImapProtocol(ch.get_email(), ch.get_password(), ch.get_host())
    ch.protocol = ch.Protocol.EXCHANGE
    exchange = ExchangeProtocol(ch.get_email(), ch.get_password(), ch.get_username())
    try:
        ch.protocol = ch.Protocol.IMAP
        imap.login()
        ch.protocol = ch.Protocol.EXCHANGE
        exchange.login()
        yield imap, exchange
    finally:
        imap.logout()
        exchange.logout()


def test_get_emails_with_mocking(mocker):
    mocked_imap = mocker.Mock()
    mocked_imap.list_folders.return_value = [
        ([b"\\HasNoChildren"], None, "INBOX"),
        ([b"\\HasNoChildren"], None, "SENT"),
        ([b"\\HasChildren"], None, "ARCHIVE"),
        ([b"\\Drafts"], None, "DRAFTS"),
    ]

    mocked_imap.search.return_value = [1]
    email_message = EmailMessage()
    email_message["Message-Id"] = "test-id"
    email_message["From"] = "sender@example.com"
    email_message["Subject"] = "Test Subject"
    email_message["To"] = "recipient@example.com"
    email_message["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
    email_message.set_content("This is the email body.")
    mocked_imap.fetch.return_value = {1: {b"RFC822": email_message.as_bytes()}}

    mocked_self = mocker.Mock()
    mocked_self.IMAP = mocked_imap
    mocked_self.logged_in = True

    # Testmethoden patchen
    mocked_self._get_folder_names = ImapProtocol._get_folder_names.__get__(mocked_self)
    mocked_self._get_emails = ImapProtocol._get_emails.__get__(mocked_self)

    # Testdaten vorbereiten
    date_filter = datetime(2024, 1, 1)

    # Aktion: get_emails aufrufen
    result = ImapProtocol.get_emails(mocked_self, date=date_filter)
    print(result)
    # Assertions: Überprüfen, ob die Ergebnisse korrekt sind
    assert len(result) == 2  # INBOX und SENT wurden verarbeitet
    assert result[0].message_id == "test-id"
    assert result[0].subject == "Test Subject"
    assert result[0].body == "This is the email body.\n"

    # Überprüfen, ob _get_folder_names korrekt gearbeitet hat
    mocked_imap.list_folders.assert_called_once()

    # Überprüfen, ob die gefilterten Ordner korrekt ignoriert wurden
    assert mocked_imap.select_folder.call_count == 2
    mocked_imap.select_folder.assert_any_call("INBOX")
    mocked_imap.select_folder.assert_any_call("SENT")
