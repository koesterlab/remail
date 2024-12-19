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
        if len(emails) == 2:
            return emails[0]
        time.sleep(0.05)
    raise TimeoutError()

@contextmanager
def email_test_context(date: datetime):
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
    """testing get_mails with date, delete with msgID,get_deleted_emails"""
    date = datetime.now(get_localzone())
    with email_test_context(date) as (imap,exchange):
        try:
            # send
            #exchange.send_email(exchange_test_email)
            imap.send_email(imap_test_email)

            #get the mail
            test_mail_ex = wait_for_email(exchange,date)
            #test_mail_im = wait_for_email(imap,date)

            #compare subjects
            assert test_mail_ex.subject == "test_imap_mail"
            #assert test_mail_im.subject == "test_exchange_mail"

            #delete mail
            exchange.delete_email(test_mail_ex.message_id,True)
            #imap.delete_email(test_mail_im.message_id,True)

            #compare for deletete mail exists
            assert len(exchange.get_emails(date)) == 0
            assert len(imap.get_emails(date)) == 0

            #get deleted mails
            message_ids_ex = exchange.get_deleted_emails([test_mail_ex.message_id])
            #message_ids_im = imap.get_deleted_emails([test_mail_im.message_id])

            #compare deleted with mail
            assert test_mail_ex.message_id == message_ids_ex[0], "Exchange deleted Fehler"
            #assert test_mail_im.message_id == message_ids_im[0], "Imap deleted Fehler"
        except Exception as e:
            raise e


