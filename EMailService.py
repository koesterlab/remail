from abc import ABC, abstractmethod
from email2 import Email, EmailReception, Attachment, Contact, RecipientKind
from imapclient import IMAPClient
from smtplib import SMTP_SSL,SMTP_SSL_PORT
import email
from email.message import EmailMessage
from datetime import datetime
from exchangelib import Credentials, Account, Message, FileAttachment, EWSDateTime, UTC
import os
import keyring
from bs4 import BeautifulSoup


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
    def send_email(self,email: Email) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractmethod
    def delete_email(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        pass
    @abstractmethod
    def get_emails(self, date : datetime = None)->list[Email]:
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
        return self.user_passwort is not None and self.user_username is not None
    
    def login(self,user:str, password:str) -> bool:
        self.user_username = user
        self.user_passwort = password
        self.IMAP.login(user, password)
    
    def logout(self) -> bool:
        self.IMAP.logout()
        self.user_passwort = None
        self.user_username = None
    
    def send_email(self, email:Email) -> bool:
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
            with open(att.filename, "rb") as f:
                file_data = f.read()
            msg.add_attachment(file_data, maintype = "text", subtype = "plain", filename = "test.txt")

        #connect/authenticate
        smtp_server = SMTP_SSL(self.SMTP_HOST, port = SMTP_SSL_PORT)
        smtp_server.login(SMTP_USER, SMTP_PASS)
        smtp_server.send_message(msg)
        
        #disconnect
        smtp_server.quit()
        pass

    def delete_email(self, uid:int) -> bool:
        """Requierment: User is logged in"""
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["UID",uid])
            if len(messages_ids)!= 0:
                    self.IMAP.delete_messages()
    
    def get_emails(self, date : datetime = None)->list[Email]:
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
            body = None
            if email_message.is_multipart():
                html_parts = []
                #iter over all parts
                for part in email_message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))

                    #get attachments part
                    if part.get_content_disposition() == "attachment":
                        filename = part.get_filename()

                        #safe attachments
                        if filename:
                            filepath = os.path.join("attachments", filename)
                            os.makedirs("attachments", exist_ok=True)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                                attachments_file_names.append(filepath)
                                print("Attachmants")
                    #get HTML parts
                    if part.get_content_disposition() == "text/html":
                        html_content = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                        html_parts.append(html_content)
                        print("HTML erkannt")

                    #get plain text from email
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True)
                        print("Text Plain")

            #get 
            else:
                body = email_message.get_payload(decode=True)
                print("Text Plain ohne multipart")

            #hier fehlt noch das date 

            listofMails += [create_email(
                                uid = Uid,
                                sender = email_message["from"],
                                subject = email_message["subject"],
                                body = body.decode("UTF-8"),
                                attachments = attachments_file_names,
                                to_recipients = email_message["to"],
                                cc_recipients = email_message["cc"],
                                bcc_recipients = email_message["bcc"],
                                date = email_message["date"],
                                html_files = html_parts)]
        return listofMails

    def get_deleted_emails(self,uids:list[str])->list[str]:
        listofUIPsIMAP = []
        for mailbox in self.IMAP.list_folders():
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["ALL"])
            for message_data in self.IMAP.fetch(messages_ids,["RFC822","UID"]).items():
                listofUIPsIMAP.append(message_data.get(b"UID"))
            self.IMAP.close_folder(mailbox)
        return uids-listofUIPsIMAP
    
    def mark_email(self,uid:str,read:bool):
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

    def mark_email(self, uid, read : bool):
        for item in self.acc.inbox.filter(message_id=uid):
            item.is_read = read
            item.save(update_fields = ["is_read"])


    def delete_email(self, uid:int) -> bool:
        """Requierment: User is logged in
        moves the email in the trash folder"""
        if not self.logged_in:
            return False
        
        for item in self.acc.inbox.filter(message_id=uid):
            item.move_to_trash()
    
    def get_deleted_emails(self, uids : list[str]):
        if not self.logged_in:
            return None
        
        server_uids = [item.message_id for item in self.acc.inbox.all()]

        return uids - server_uids


    def get_emails(self, date : datetime = None)->list[Email]:
        
        if not self.logged_in:
            return None

        result = []
        if not date:
            for item in self.acc.inbox.all():
                result += self.get_email_exchange(item)
        else:
            start_date = EWSDateTime.from_datetime(date).astimezone(UTC)
            for item in self.acc.inbox.filter(datetime_received__gte = start_date):
                result += self.get_email_exchange(item)
        return result

    #Attachments sind leer
    def get_email_exchange(self, item):
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

def imap_test():
    imap = ImapProtocol()
    test = Email(
        
        subject="TestBCC",
        body="Test time!!",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to)],
        #attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")])
    )
    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("thatchmilo35@gmail.com","mgtszvrhgkphxghm")
    print("IMAP Logged_in: ",imap.logged_in)

    imap.send_email(test)
    print("sent?")
    
    #listofmails = imap.get_emails(datetime(2024,11,29,9,11,0))
    #print(len(listofmails))
    #print(listofmails[0].body)
    
    #print("body" ,listofmails[0].body,"id",listofmails[0].id )

    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

def exchange_test():
    exchange = ExchangeProtocol()


    #exchange

    test = Email(
        
        subject="Betreff",
        body="World",
        recipients=[EmailReception(contact=(Contact(email_address ="thatchmilo35@gmail.com")),kind=RecipientKind.to)],
        attachments=[Attachment(filename="path")])


    print("Exchange Logged_in: ",exchange.logged_in)
    exchange.login("praxisprojekt-remail@uni-due.de",keyring.get_password("remail/exchange","praxisprojekt-remail@uni-due.de"))
    print("Exchange Logged_in: ",exchange.logged_in)
    emails = exchange.get_emails(datetime(2024,11,29,10,15))
    print(emails)
    exchange.send_email(test)
    exchange.logout()
    print("Exchange Logged_in: ",exchange.logged_in)

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
    print("Hallo",attachments)
    attachments_class = [Attachment(filename) for filename in attachments]

    recipients = [EmailReception(contact = get_contact(recipient), kind = RecipientKind.to) for recipient in to_recipients]
    if cc_recipients:
        recipients += [EmailReception(contact = get_contact(recipient), kind = RecipientKind.cc) for recipient in cc_recipients]
    if bcc_recipients:
        recipients += [EmailReception(contact = get_contact(recipient), kind = RecipientKind.bcc) for recipient in bcc_recipients]

    return Email(
        id = uid,
        sender_contact= sender_contact,
        subject=subject,
        body=body,
        attachments=attachments_class,
        recipients=recipients,
        date=date
    )

def get_contact(email : str) -> Contact:
    return Contact(email_address=email)

if __name__ == "__main__":
    print("Starte Tests")
    imap_test()
    #exchange_test()
    print("Tests beendet")
    
    

