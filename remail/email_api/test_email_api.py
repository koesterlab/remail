from object import Email, EmailReception, Attachment, Contact, RecipientKind
from service import *
import time



def test_mails():
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
    date = datetime.now(get_localzone())
    imap = ImapProtocol()
    exchange = ExchangeProtocol()
    #Logins
    assert imap.login()
    assert imap.logged_in
    assert exchange.login()
    assert exchange.logged_in
    # senden mit exchange und auslesen mit imap
    assert exchange.send_email(exchange_test_email)
    time.sleep(9)
    test_mail = imap.get_emails(date)[0]
    assert test_mail.subject == "test_exchange_mail"
    #löschen der Email mit imap
    assert imap.delete_email(test_mail.id)
    assert len(imap.get_emails(date)) == 0
    # senden mit imap und auslesen mit exchange
    assert imap.send_email(imap_test_email)
    time.sleep(9)
    test_mail = exchange.get_emails(date)[0]
    assert test_mail.subject == "test_imap_mail"
    #löschen der Email mit exchange
    assert exchange.delete_email(test_mail.id)
    assert len(exchange.get_emails(date)) == 0
    #Logout
    assert imap.logout()
    assert not imap.logged_in
    assert exchange.logout()
    assert not exchange.logged_in


