from abc import ABC, abstractclassmethod
from dataclasses import dataclass

@dataclass
class Email:
    senderEmailAddr:str
    recipientEmailAddrs:list[str]
    CcList:list[str]
    BccList:list[str]
    Header:str
    Body:str
    attachments:list[str]



class ProtocolTemplate(ABC):
    @abstractclassmethod
    def login(self,user:str, password:str) -> bool:
        pass
    @abstractclassmethod
    def logout(self) -> bool:
        pass
    @abstractclassmethod
    def sendEmail(self,Email:Email) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractclassmethod
    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractclassmethod
    def getEmails(self)->list[Email]:
        pass