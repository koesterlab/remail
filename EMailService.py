from abc import ABC, abstractmethod
from dataclasses import dataclass
from email2 import *
from imaplib import IMAP4_SSL
from imapclient import IMAPClient
from smtplib import SMTP_SSL,SMTP_SSL_PORT
import email

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
    def sendEmail(self,email: Email) -> bool:
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

    IMAP = IMAPClient(host,use_uid=True)
    SMTP_HOST = host

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
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["UID",uid])
            if len(messages_ids)!= 0:
                    self.IMAP.delete_messages()
    
    def getEmails(self)->list[Email]:
        listofMails = list[Email]
        self.IMAP.select_folder("INBOX")
        messages_ids = self.IMAP.search()
        for uid,message_data in self.IMAP.fetch(messages_ids,"RFC822").items():
            email_message = email.message_from_bytes(message_data[b"RFC822"])
            newEmail = Email()
            newEmail.id = uid
            newEmail.sender = email_message.get("FROM")
            newEmail.subject = email_message.get("SUBJECT")
            if email_message.is_multipart():
                for part in email_message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        newEmail.body = part.get_payload(decode=True)
                    break

            else:
                newEmail.body = email_message.get_payload(decode=True)
            listofMails.append(newEmail)
        return listofMails

from exchangelib import Credentials, Account, Message, Configuration

class ExchangeProtocol(ProtocolTemplate):
    

    def __init__(self):
        self.cred = None
        self.acc = None
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    def login(self,user:str, password:str) -> bool:
        try:
            self.cred = Credentials("ude-1729267167",password)
            self.acc = Account(user, credentials=self.cred, autodiscover=True)
            self._logged_in = True
            return True
        except:
            return False
    
    def logout(self) -> bool:
        self.acc = None
        self.cred = None
        self._logged_in = False
        return True
    
    def sendEmail(self,email:Email) -> bool:
        """Requierment: User is logged in"""
        if not self.logged_in:
            return False
        

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


        m = Message(
            account = self.acc,
            subject = email.subject,
            body = email.body,
            to_recipients = to,
            cc_recipients = cc,
            bcc_recipients = bcc
        )
        m.send()

    def mark_email(self, uid, read : bool):
        for item in self.acc.inbox.filter(message_id=uid):
            item.is_read = read
            item.save(update_fields = ["is_read"])


    def deleteEmail(self, uid:int) -> bool:
        """Requierment: User is logged in
        moves the email in the trash folder"""
        if not self.logged_in:
            return False
        
        for item in self.acc.inbox.filter(message_id=uid):
            item.move_to_trash()
    
    def getEmails(self)->list[Email]:
        
        if not self.logged_in:
            return None

        result = []
        for item in self.acc.inbox.all():
            result += [(item.subject,item.message_id)]
        return result

def imap_test():
    imap = ImapProtocol()
    test = Email(
        
        subject="Hello",
        body="World",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to)])

    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("thatchmilo35@gmail.com","mgtszvrhgkphxghm")
    print("IMAP Logged_in: ",imap.logged_in)

    #imap.sendEmail(test)
    print("sent?")
    
    listofmails = imap.getEmails()
    print(listofmails[0].sender)

    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

def exchange_test():
    exchange = ExchangeProtocol()


    #exchange
    #import keyring

    print("Exchange Logged_in: ",exchange.logged_in)
    #exchange.login("praxisprojekt-remail@uni-due.de",keyring.get_password("remail/exchange","praxisprojekt-remail@uni-due.de"))
    print("Exchange Logged_in: ",exchange.logged_in)
    emails = exchange.getEmails()
    exchange.mark_email(emails[0][1],False)
    exchange.logout()
    print("Exchange Logged_in: ",exchange.logged_in)

if __name__ == "__main__":
    print("Starte Tests")
    imap_test()
    #exchange_test()
    print("Tests beendet")
    
    

