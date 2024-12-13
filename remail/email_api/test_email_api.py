from remail.database_api.models import Email, EmailReception,Contact, RecipientKind
from remail.email_api.service import ImapProtocol,ExchangeProtocol,ProtocolTemplate
import remail.email_api.credentials_helper as ch
from datetime import datetime
from tzlocal import get_localzone
from contextlib import contextmanager

import time

imap_test_email = Email(
        
        subject="test_imap_mail",
        body="Test!!",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to)],
        #attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")]
    )

exchange_test_email = Email(
        
        subject="test_exchange_mail",
        body="Test!!",
        recipients=[EmailReception(contact=(Contact(email_address ="thatchmilo35@gmail.com")), kind=RecipientKind.to)],
        #attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")]
    )



def wait_for_email(protocol:ProtocolTemplate,dtime:datetime,timeout:int = 30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        emails = protocol.get_emails(dtime)
        if len(emails) == 1:
            return emails[0]
        time.sleep(0.05)
    raise TimeoutError()

@contextmanager
def email_test_context():
    ch.protocol = ch.Protocol.IMAP
    imap = ImapProtocol(ch.get_email(),ch.get_password(),ch.get_host())
    ch.protocol = ch.Protocol.EXCHANGE
    exchange = ExchangeProtocol(ch.get_email(),ch.get_password(),ch.get_username())
    try:
        ch.protocol = ch.Protocol.IMAP
        imap.login()
        ch.protocol = ch.Protocol.EXCHANGE
        exchange.login()
        yield imap,exchange
    finally:
        imap.logout()
        exchange.logout()




def test_mails():
    """testing get_mails with date, delete with msgID"""
    with email_test_context() as (imap,exchange):
        try:
            date = datetime.now(get_localzone())
            # senden mit exchange und auslesen mit imap
            exchange.send_email(exchange_test_email)
            test_mail = wait_for_email(imap,date)
            assert test_mail.subject == "test_exchange_mail"
            #löschen der Email mit imap
            imap.delete_email(test_mail.message_id)
            assert len(imap.get_emails(date)) == 0
            #schauen ob die email deleted ist
            message_ids = imap.get_deleted_emails([test_mail])
            assert test_mail.message_id == message_ids[0], "Imap deleted Fehler"
            # senden mit imap und auslesen mit exchange
            imap.send_email(imap_test_email)
            test_mail = wait_for_email(exchange,date)
            assert test_mail.subject == "test_imap_mail"
            #löschen der Email mit exchange
            exchange.delete_email(test_mail.message_id)
            assert len(exchange.get_emails(date)) == 0
            message_ids = exchange.get_deleted_emails([test_mail])
            assert test_mail.message_id == message_ids[0], "Exchange deleted Fehler"
        except Exception:
            return


