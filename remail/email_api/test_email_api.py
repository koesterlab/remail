import sys, os
print(sys.path)
print(os.getcwd())
print(os.listdir("."))

from remail.database.models import Email, EmailReception, Contact, RecipientKind
from remail.email_api.service import ImapProtocol, ExchangeProtocol
import remail.email_api.credentials_helper as ch
from contextlib import contextmanager
from datetime import datetime
from email.utils import format_datetime
from email.message import EmailMessage
from exchangelib import Message, EWSDateTime, Mailbox
from pytz import timezone

from remail.controller import controller


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


def test_get_emails_with_mocking_imap(mocker):
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
    mocked_self.controller = controller
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


def test_get_emails_with_mocking_exchange(mocker):
    mocked_exchange = mocker.Mock()

    mocked_self = mocker.Mock()
    mocked_self.acc = mocked_exchange
    mocked_self.logged_in = True

    item = Message()
    item.message_id = "test-id"
    item.datetime_received = EWSDateTime.from_datetime(
        datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone("UTC"))
    )
    item.text_body = "This is the email body.\n"
    item.sender = Mailbox()
    item.sender.email_address = "sender@example.com"
    item.subject = "Test Subject"
    recipient = Mailbox()
    recipient.email_address = "recipient@example.com"
    item.to_recipients = [recipient]

    date_filter = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone("UTC"))

    mocked_self.controller = controller
    mocked_self._get_items.return_value = [item]
    mocked_self._get_email_exchange = ExchangeProtocol._get_email_exchange.__get__(
        mocked_self
    )

    result = ExchangeProtocol.get_emails(mocked_self, date=date_filter)
    print(result)
    # Assertions: Überprüfen, ob die Ergebnisse korrekt sind
    assert len(result) == 1  # INBOX und SENT wurden verarbeitet
    assert result[0].message_id == "test-id"
    assert result[0].subject == "Test Subject"
    assert result[0].body == "This is the email body.\n"
