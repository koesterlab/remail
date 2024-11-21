from abc import ABC, abstractmethod
from dataclasses import dataclass
from email2 import Email


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
    
    @property
    def logged_in(self) -> bool:
        pass
    
    def login(self,user:str, password:str) -> bool:
        pass
    
    def logout(self) -> bool:
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

