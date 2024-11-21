from abc import ABC, abstractmethod
from dataclasses import dataclass
from email2 import Email
from imaplib import IMAP4

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
    host = None

    IMAP = None
    

    @property
    def logged_in(self) -> bool:
        return self.user_passwort != None and self.user_username != None
    
    def login(self,user:str, password:str) -> bool:
        self.IMAP = IMAP4(self.host)
        self.user_username = user
        self.user_passwort = password
        self.IMAP.login(user, password)
        pass
    
    def logout(self) -> bool:
        self.IMAP.logout()
        self.user_passwort = None
        self.user_username = None
        pass
    
    def sendEmail(self,Email:Email) -> bool:
        """Requierment: User is logged in"""
        pass

    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    
    def getEmails(self)->list[Email]:
        pass

class ExchangeProtocol(ProtocolTemplate):
    
    username : str = ""
    password : str = ""

    @property
    def logged_in(self) -> bool:
        return self.username != "" and self.password != ""

    def login(self,user:str, password:str) -> bool:
        self.username = user
        self.password = password
        return True
    
    def logout(self) -> bool:
        self.username = ""
        self.password = ""
        return True
    
    def sendEmail(self,Email:Email) -> bool:
        """Requierment: User is logged in"""
        pass

    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    
    def getEmails(self)->list[Email]:
        pass

if __name__ == "__main__":
    imap = ImapProtocol()
    exchange = ExchangeProtocol()

    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("","")
    print("IMAP Logged_in: ",imap.logged_in)
    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

    #exchange

    print("Exchange Logged_in: ",exchange.logged_in)
    exchange.login("ude-1729267167","6jTDTk6hS3j^b%@tw")
    print("Exchange Logged_in: ",exchange.logged_in)
    exchange.logout()
    print("Exchange Logged_in: ",exchange.logged_in)

