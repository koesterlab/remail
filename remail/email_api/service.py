from abc import ABC, abstractmethod
from remail.email_api.object import Email, EmailReception, Attachment, Contact, RecipientKind
from imapclient import IMAPClient
from smtplib import SMTP_SSL,SMTP_SSL_PORT
import email
from email.message import EmailMessage
from datetime import datetime
from exchangelib import Credentials, Account, Message, FileAttachment, EWSDateTime, UTC
import os
import keyring
from bs4 import BeautifulSoup
import mimetypes

class ProtocolTemplate(ABC):
    
    @property
    @abstractmethod
    def logged_in(self) -> bool:
        pass
    
    @abstractmethod
    def login(self) -> bool:
        pass

    @abstractmethod
    def logout(self) -> bool:
        pass

    @abstractmethod
    def send_email(self,email: Email) -> bool:
        """Requierment: User is logged in"""
        pass

    @abstractmethod
    def get_deleted_emails(self, uids: list[str]) -> list[str]:
        pass

    @abstractmethod
    def mark_email(self, uid: str, read: bool) -> bool:
        pass

    @abstractmethod
    def delete_email(self, uid: str) -> bool:
        """Requierment: User is logged in"""
        pass

    @abstractmethod
    def get_emails(self, date: datetime = None)->list[Email]:
        pass

class ImapProtocol(ProtocolTemplate):
    
    #email address
    user_username = None
    #or imappassword
    user_password = None
    host = "imap.gmail.com"
    def __init__(self):
        self.IMAP = IMAPClient(self.host,use_uid=True)

    SMTP_HOST = host

    @property
    def logged_in(self) -> bool:
        return self.user_password is not None and self.user_username is not None
    
    def login(self) -> bool:
        if self.logged_in: 
            return True
        try:
            self.user_username = "thatchmilo35@gmail.com"
            self.user_password = keyring.get_password("remail/IMAP","thatchmilo35@gmail.com")
            self.IMAP.login(self.user_username, self.user_password)
            return True
        except Exception:
            return False


    def logout(self) -> bool:
        try:
            self.IMAP.logout()
            self.user_password = None
            self.user_username = None
            return True
        except Exception:
            return False
        
    def send_email(self, email:Email) -> bool:
        """Requierment: User is logged in"""

        if not self.logged_in:
            return False

        SMTP_USER = self.user_username
        SMTP_PASS = self.user_password

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
        msg = EmailMessage()
        msg['Subject'] = email.subject
        msg['From'] = from_email
        msg['To'] = to
        msg['Cc'] = cc
        if len(bcc) > 0:
            msg['Bcc'] = ",".join(bcc)
        msg.set_content(email.body)

        #attachment
        for att in email.attachments:
            filename = os.path.basename(att.filename)  # Sanitize filename
            if not os.path.exists(att.filename) or not os.path.isfile(att.filename):
                continue
            with open(os.path.abspath(att.filename), "rb") as file:
                file_data = file.read()
                type = mimetypes.guess_type(file.name)[0].split("/")
                main_type = type[0]
                sub_type = type[1]
            msg.add_attachment(file_data, maintype = main_type, subtype = sub_type, filename = filename)

        #connect/authenticate
        smtp_server = SMTP_SSL(self.SMTP_HOST, port = SMTP_SSL_PORT)
        smtp_server.login(SMTP_USER, SMTP_PASS)
        smtp_server.send_message(msg)
        
        #disconnect
        smtp_server.quit()
        return True

    def delete_email(self, uid:str) -> bool:
        """Requierment: User is logged in"""
        if not self.logged_in: 
            return False
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["UID",uid])
            if len(messages_ids)!= 0:
                    self.IMAP.delete_messages(messages_ids)
                    self.IMAP.expunge()
    
    def get_emails(self, date : datetime = None)->list[Email]:
        if not self.logged_in: 
            return None
        listofMails = []
        self.IMAP.select_folder("INBOX")
        if date is not None:
            messages_ids = self.IMAP.search([u'SINCE',date])
        else: 
            messages_ids = self.IMAP.search(["ALL"])
        for msgid,message_data in self.IMAP.fetch(messages_ids,["RFC822","UID"]).items():
            email_message = email.message_from_bytes(message_data[b"RFC822"])
            Uid = message_data.get(b"UID")
            attachments_file_names = []
            html_parts = []
            body = None
            if email_message.is_multipart():                
                #iter over all parts
                for part in email_message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    #get attachments part
                    if part.get_content_disposition() == "attachment":
                        filename = part.get_filename()

                        #safe attachments
                        if filename:
                            filepath = os.path.join("attachments", os.path.basename(filename))
                            os.makedirs("attachments", exist_ok=True)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                attachments_file_names.append(filepath)
                    #get HTML parts
                    if part.get_content_disposition() == "text/html":
                        html_content = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                        html_parts.append(html_content)

                    #get plain text from email
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True)

            #get 
            else:
                body = email_message.get_payload(decode=True)

            #hier fehlt noch das date 

            if body:
                body_content = body.decode("UTF-8")
            else:
                body_content = ""

            listofMails += [create_email(
                                uid = Uid,
                                sender = email_message["from"],
                                subject = email_message["subject"],
                                body = body_content,
                                attachments = attachments_file_names,
                                to_recipients = email_message["to"],
                                cc_recipients = email_message["cc"],
                                bcc_recipients = email_message["bcc"],
                                date = email_message["date"],
                                html_files = html_parts)]
        return listofMails

    def get_deleted_emails(self,uids:list[str])->list[str]:
        if not self.logged_in: 
            return None
        listofUIPsIMAP = []
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["ALL"])
            for message_data in self.IMAP.fetch(messages_ids,["RFC822","UID"]).items():
                listofUIPsIMAP.append(message_data.get(b"UID"))
            self.IMAP.close_folder(mailbox)
        return list(set(uids)-set(listofUIPsIMAP))
    
    def mark_email(self,uid:str,read:bool) -> bool:
        if not self.logged_in: 
            return False
        if read:
            self.IMAP.add_flags(uid,["SEEN"])
        else:
            self.IMAP.remove_flags(uid,["SEEN"])



class ExchangeProtocol(ProtocolTemplate):
    

    def __init__(self):
        self.cred = None
        self.acc = None
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    def login(self) -> bool:
        if self.logged_in:
            return True
        
        user = "praxisprojekt-remail@uni-due.de"
        password = keyring.get_password("remail/exchange","praxisprojekt-remail@uni-due.de")

        try:
            self.cred = Credentials("ude-1729267167",password)
            self.acc = Account(user, credentials=self.cred, autodiscover=True)
            self._logged_in = True
            return True
        except Exception:
            return False
    
    def logout(self) -> bool:
        self.acc = None
        self.cred = None
        self._logged_in = False
        return True
    
    def send_email(self,email:Email) -> bool:
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

        for attachement in email.attachments:
            
            path = attachement.filename
            if not os.path.exists(path): 
                continue
            with open(path,"b+r") as f:
                content = f.read()
                att = FileAttachment(name = os.path.basename(path), content = content)
                m.attach(att)

        m.send()

    def mark_email(self, uid: str, read : bool) -> bool:
        if not self.logged_in:
            return False
        for item in self.acc.inbox.filter(message_id=uid):
            item.is_read = read
            item.save(update_fields = ["is_read"])
        return True


    def delete_email(self, uid:str) -> bool:
        """Requierment: User is logged in
        moves the email in the trash folder"""
        if not self.logged_in:
            return False
        
        for item in self.acc.inbox.filter(message_id=uid):
            item.move_to_trash()
    
    def get_deleted_emails(self, uids : list[str]) -> list[str]:
        if not self.logged_in:
            return None
        
        server_uids = [item.message_id for item in self.acc.inbox.all()]

        return list(set(uids) - set(server_uids))


    def get_emails(self, date : datetime = None)->list[Email]:
        
        if not self.logged_in:
            return None

        os.makedirs("attachments", exist_ok=True)
        result = []
        if not date:
            for item in self.acc.inbox.all():
                result += self._get_email_exchange(item)
        else:
            start_date = EWSDateTime.from_datetime(date).astimezone(UTC)
            for item in self.acc.inbox.filter(datetime_received__gte = start_date):
                result += self._get_email_exchange(item)
        return result

    #Attachments sind leer
    def _get_email_exchange(self, item):
        attachments = []
        for attachment in item.attachments:
            if isinstance(attachment, FileAttachment):
                local_path = os.path.join('attachments', attachment.name)
                with open(local_path, 'wb') as f:
                    f.write(attachment.content)
                    attachments += [local_path]
        
        ews_datetime_str = item.datetime_received.astimezone()
        parsed_datetime = datetime.fromisoformat(ews_datetime_str.ewsformat())

        soup = BeautifulSoup(item.body,"html.parser")
        if (bool(soup.find())):
            body = soup.get_text()
            html = [item.body]
        else:
            body = item.body
            html = []

        return [create_email(
                uid = item.message_id, 
                sender= item.sender,
                subject = item.subject, 
                body = body, 
                attachments=attachments, 
                to_recipients=item.to_recipients,
                cc_recipients=[],
                bcc_recipients=[],
                date = parsed_datetime,
                html_files=html
                )]

#-------------------------------------------------

def create_email(
        uid : str,
        sender : str, 
        subject: str, 
        body: str, 
        attachments: list[str], 
        to_recipients: list[str],
        cc_recipients: list[str],
        bcc_recipients: list[str],
        date: datetime, 
        html_files: list[str] = None 
        ) -> Email:
    
    sender_contact = get_contact(sender)
    

    recipients = [EmailReception(contact = get_contact(recipient), kind = RecipientKind.to) for recipient in to_recipients]
    if cc_recipients:
        recipients += [EmailReception(contact = get_contact(recipient), kind = RecipientKind.cc) for recipient in cc_recipients]
    if bcc_recipients:
        recipients += [EmailReception(contact = get_contact(recipient), kind = RecipientKind.bcc) for recipient in bcc_recipients]

    email =  Email(
        sender_contact= sender_contact,
        subject=subject,
        body=body,
        recipients=recipients,
        date=date
    )

    attachments_class = [Attachment(filename = filename, email = email) for filename in attachments]

    email.attachments = attachments_class

    return email

def get_contact(email : str) -> Contact:
    return Contact(email_address=email)

def save_credentials():
    
    password_exchange = keyring.get_password("remail/exchange","praxisprojekt-remail@uni-due.de")
    password_imap = keyring.get_password("remail/IMAP","thatchmilo35@gmail.com")
    if not password_exchange:
        password = input("Gebe das Exchangepasswort ein, um es auf deinem Rechner zu hinterlegen: ")
        keyring.set_password("remail/exchange","praxisprojekt-remail@uni-due.de",password)
    if not password_imap:
        password = input("Gebe das IMAPpasswort ein, um es auf deinem Rechner zu hinterlegen: ")
        keyring.set_password("remail/IMAP","thatchmilo35@gmail.com",password)

def change_credentials_exchange():
    password = input("Gebe das Exchangepasswort ein, um es auf deinem Rechner zu hinterlegen: ")
    keyring.set_password("remail/exchange","praxisprojekt-remail@uni-due.de",password)
def change_credentials_imap():
    password = input("Gebe das IMAPpasswort ein, um es auf deinem Rechner zu hinterlegen: ")
    keyring.set_password("remail/IMAP","thatchmilo35@gmail.com",password)

def test_mails():
    imap_test_email = Email(
        
        subject="test_imap_mail",
        body="Test!!",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to)],
        attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")]
    )
    exchange_test_email = Email(
        
        subject="test_exchange_mail",
        body="Test!!",
        recipients=[EmailReception(contact=(Contact(email_address ="thatchmilo35@gmail.com")), kind=RecipientKind.to)],
        #attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")]
    )
    time = datetime.now()
    imap = ImapProtocol()
    exchange = ExchangeProtocol()
    #Logins
    assert imap.login() == True
    assert imap.logged_in == True
    assert exchange.login() == True
    assert exchange.logged_in == True
    # senden mit exchange und auslesen mit imap
    assert exchange.send_email(exchange_test_email) == True
    test_mail = imap.get_emails(time)[0]
    assert test_mail.subject == "test_exchange_mail"
    #löschen der Email mit imap
    assert imap.delete_email(test_mail.id) == True
    assert len(imap.get_emails(time)) == 0
    # senden mit imap und auslesen mit exchange
    assert imap.send_email(imap_test_email) == True
    test_mail = exchange.get_emails(time)[0]
    assert test_mail.subject == "test_imap_mail"
    #löschen der Email mit exchange
    assert exchange.delete_email(test_mail.id) == True
    assert len(exchange.get_emails(time)) == 0
    #Logout
    assert imap.logout() == True
    assert imap.logged_in == False
    assert exchange.logout() == True
    assert exchange.logged_in == False
    
    

