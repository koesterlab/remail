from abc import ABC, abstractmethod
from dataclasses import dataclass
from email2 import Email
from imaplib import IMAP4_SSL
from imapclient import IMAPClient


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
    
    user_username = None
    user_passwort = None
    host = "imap.gmail.com"

    IMAP = IMAPClient(host)
    

    @property
    def logged_in(self) -> bool:
        return self.user_passwort != None and self.user_username != None
    
    def login(self,user:str, password:str) -> bool:
        self.user_username = user
        self.user_passwort = password
        self.IMAP.login(user, password)
    
    def logout(self) -> bool:
        self.IMAP.logout()
        self.user_passwort = None
        self.user_username = None
    
    def sendEmail(self,Email:Email) -> bool:
        """Requierment: User is logged in"""
        pass

    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            status, messages = self.IMAP.search("")
            if status == "OK":
                self.IMAP.store(uid,"+Flags","\\Deleted")
                self.IMAP.expunge()
            self.IMAP.close()
    
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

    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("thatchmilo35@gmail.com","mgtszvrhgkphxghm")
    print("IMAP Logged_in: ",imap.logged_in)
    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

    #exchange

    print("Exchange Logged_in: ",exchange.logged_in)
    exchange.login("praxisprojekt-remail@uni-due.de","6jTDTk6hS3j^b%@tw")
    print("Exchange Logged_in: ",exchange.logged_in)
    exchange.logout()
    print("Exchange Logged_in: ",exchange.logged_in)

