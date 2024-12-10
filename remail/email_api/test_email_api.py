from object import Email, EmailReception,Contact, RecipientKind
from service import ImapProtocol,ExchangeProtocol,ProtocolTemplate
from datetime import datetime
from tzlocal import get_localzone

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

def email_test_context():
    imap = ImapProtocol()
    exchange = ExchangeProtocol()
    try:
        assert imap.login(), "IMAP login failed"
        assert exchange.login(), "Exchange login failed"
        yield imap,exchange
    finally:
        imap.logout()
        exchange.logout()




def test_mails():
    with email_test_context() as (imap,exchange):
        try:
            date = datetime.now(get_localzone())
            #Logins
            assert imap.login()
            assert imap.logged_in
            assert exchange.login()
            assert exchange.logged_in
            # senden mit exchange und auslesen mit imap
            assert exchange.send_email(exchange_test_email)
            test_mail = wait_for_email(imap,date)
            assert test_mail.subject == "test_exchange_mail"
            #löschen der Email mit imap
            assert imap.delete_email(test_mail.id)
            assert len(imap.get_emails(date)) == 0
            # senden mit imap und auslesen mit exchange
            assert imap.send_email(imap_test_email)
            test_mail = wait_for_email(exchange,date)
            assert test_mail.subject == "test_imap_mail"
            #löschen der Email mit exchange
            assert exchange.delete_email(test_mail.id)
            assert len(exchange.get_emails(date)) == 0
            #Logout
            assert imap.logout()
            assert not imap.logged_in
            assert exchange.logout()
            assert not exchange.logged_in
        except Exception:
            return


