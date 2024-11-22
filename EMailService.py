from abc import ABC, abstractmethod
from dataclasses import dataclass
from email2 import *
from imaplib import IMAP4_SSL
from smtplib import SMTP_SSL, SMTP_SSL_PORT

class ProtocolTemplate(ABC):
    
    @property
    @abstractmethod
    def logged_in(self) -> bool:
        pass
    
    @abstractmethod
    def login(self,user:str, password:str) -> bool:
        pass
    @abstractmethod
    def logout(self) -> bool:
        pass
    @abstractmethod
    def sendEmail(self,Email: Email) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractmethod
    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractmethod
    def getEmails(self)->list[Email]:
        pass

class ImapProtocol(ProtocolTemplate):
    
    #email address
    user_username = None
    #or imappassword
    user_passwort = None
    host = "imap.gmail.com"

    IMAP = IMAP4_SSL(host)
    SMTP_HOST = host

    @property
    def logged_in(self) -> bool:
        return self.user_passwort != None and self.user_username != None
    
    def login(self,user:str, password:str) -> bool:
        self.user_username = user
        self.user_passwort = password
        self.IMAP.login(user, password)
        pass
    
    def logout(self) -> bool:
        self.IMAP.logout()
        self.user_passwort = None
        self.user_username = None
        pass
    
    def sendEmail(self, email:Email) -> bool:
        """Requierment: User is logged in"""
        SMTP_USER = self.user_username
        SMTP_PASS = self.user_passwort

        to = []
        cc = []
        bcc = []
        for recipent in email.recipients:
            match (recipent.kind):
                case RecipientKind.to:
                    to += [recipent.contact.email_address]
                case RecipientKind.cc:
                    cc += [recipent.contact.email_address]
                case RecipientKind.bcc:
                    bcc += [recipent.contact.email_address]

        #craft email
        from_email = SMTP_USER
        to_emails = to
        body = email.body
        headers = f"From: {from_email}\r\n"
        headers += f"To: {', '.join(to_emails)}\r\n"
        headers += f"Subject: {email.subject}\r\n"
        email_message = headers + "\r\n" + body

        #connect/authenticate
        smtp_server = SMTP_SSL(self.SMTP_HOST, port = SMTP_SSL_PORT)
        smtp_server.set_debuglevel(1)
        smtp_server.login(SMTP_USER, SMTP_PASS)
        smtp_server.sendmail(from_email, to_emails, email_message)
        
        #disconnect
        smtp_server.quit()
        pass

    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    
    def getEmails(self)->list[Email]:
        pass

from exchangelib import Credentials, Account, Message, Configuration

class ExchangeProtocol(ProtocolTemplate):
    

    cred : Credentials | None = None
    acc = None

    @property
    def logged_in(self) -> bool:
        return True #self.cred != None and self.acc != None

    def login(self,user:str, password:str) -> bool:
        self.cred = Credentials("ude-1729267167",password)
        #config = Configuration(self.cred,"mailout.uni-due.de")
        self.acc = Account(user, credentials=self.cred, autodiscover=True)
        return True
    
    def logout(self) -> bool:
        self.acc = None
        self.cred = None
        return True
    
    def sendEmail(self,Email:Email) -> bool:
        """Requierment: User is logged in"""
        if not self.logged_in:
            return False
        m = Message(
            account = self.acc,
            subject = "Test Subject",
            body = "Dies ist der Inhalt",
            to_recipients = ["thatchmilo35@gmail.com"]
        )
        m.send()

    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    
    def getEmails(self)->list[Email]:
        pass

if __name__ == "__main__":
    imap = ImapProtocol()
    exchange = ExchangeProtocol()

    	
    test = Email(
        
        subject="Hello",
        body="World",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to)])

    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("thatchmilo35@gmail.com","mgtszvrhgkphxghm")
    print("IMAP Logged_in: ",imap.logged_in)

    imap.sendEmail(test)
    print("sent?")
    
    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

    #exchange

    #print("Exchange Logged_in: ",exchange.logged_in)
    #exchange.login("praxisprojekt-remail@uni-due.de","6jTDTk6hS3j^b%@tw")
    #print("Exchange Logged_in: ",exchange.logged_in)
    #exchange.logout()
    #print("Exchange Logged_in: ",exchange.logged_in)

