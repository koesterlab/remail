from abc import ABC, abstractmethod
from email2 import Email, EmailReception, Attachment, Contact, RecipientKind
#from imaplib import IMAP4_SSL
from imapclient import IMAPClient
from smtplib import SMTP_SSL,SMTP_SSL_PORT
import email
from email.message import EmailMessage
from datetime import date


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
    def get_emails(self, date : date)->list[Email]:
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
        #not working
        #msg['Bcc'] = bcc
        msg.set_content(email.body)

        #attachment
        with open(email.attachments[0].filename, "rb") as f:
            file_data = f.read()
        msg.add_attachment(file_data, maintype = "text", subtype = "plain", filename = "test.txt")

        #connect/authenticate
        smtp_server = SMTP_SSL(self.SMTP_HOST, port = SMTP_SSL_PORT)
        smtp_server.set_debuglevel(1)
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
    
    def get_emails(self, date : date)->list[Email]:
        listofMails = []
        self.IMAP.select_folder("INBOX")
        messages_ids = self.IMAP.search(["ALL"])
        for msgid,message_data in self.IMAP.fetch(messages_ids,["RFC822","UID"]).items():
            email_message = email.message_from_bytes(message_data[b"RFC822"])
            Uid = message_data.get(b"UID")
            html_file_names = []
            attachments_file_names = []
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
                    #get HTML parts
                    if part.get_content_disposition() == "text/html":
                        html_content = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8")
                        html_parts.append(html_content)

                    #get plain text from email
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True)
                    break

                #safe HTML parts
                if html_parts:
                    for i,html in enumerate(html_parts):
                        htmlfilename = f"email_{Uid}_part_{i+1}.html"
                        with open(htmlfilename,"w",encoding="utf-8") as f:
                            f.write(html)
                            html_file_names.append(htmlfilename)
            #get 
            else:
                body = email_message.get_payload(decode=True)

            listofMails += [create_email(
                                uid = Uid,
                                sender = email_message["from"],
                                subject = email_message["subject"],
                                body = body,
                                attachments = attachments_file_names,
                                to_recipients = email_message["to"],
                                cc_recipients = email_message["cc"],
                                bcc_recipients = email_message["bcc"],
                                html_files = html_file_names)]
        return listofMails


from exchangelib import Credentials, Account, Message, FileAttachment
import os 

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
            if not os.path.exists(path): continue
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
    
    def get_emails(self, date : date)->list[Email]:
        
        if not self.logged_in:
            return None

        result = []
        for item in self.acc.inbox.all():
            attachments = []
            for attachment in item.attachments:
                if isinstance(attachment, FileAttachment):
                    local_path = os.path.join('attachments', attachment.name)
                    with open(local_path, 'wb') as f:
                        f.write(attachment.content)
            result += [create_email(
                uid = item.message_id, 
                sender= item.sender,
                subject = item.subject, 
                body = item.body, 
                attachments=attachments, 
                to_recipients=item.to_recipients,
                cc_recipients=[],
                bcc_recipients=[])]
        return result

#-------------------------------------------------

def imap_test():
    imap = ImapProtocol()
    test = Email(
        
        subject="Hellololo",
        body="World i wanna finally go home today!!!!",
        recipients=[EmailReception(contact=(Contact(email_address ="praxisprojekt-remail@uni-due.de")), kind=RecipientKind.to),EmailReception(contact=(Contact(email_address ="toadbella@gmail.com")), kind=RecipientKind.to)],
        attachments=[Attachment(filename=r"C:\Users\toadb\Documents\ReinventingEmail\test.txt")])

    print("IMAP Logged_in: ",imap.logged_in)
    imap.login("thatchmilo35@gmail.com","mgtszvrhgkphxghm")
    print("IMAP Logged_in: ",imap.logged_in)

    imap.send_email(test)
    print("sent?")
    
    listofmails = imap.get_emails()
    #print("body" ,listofmails[0].body,"id",listofmails[0].id )

    imap.logout()
    print("IMAP Logged_in: ",imap.logged_in)

def exchange_test():
    exchange = ExchangeProtocol()


    #exchange
    #import keyring

    test = Email(
        
        subject="Betreff",
        body="World",
        recipients=[EmailReception(contact=(Contact(email_address ="thatchmilo35@gmail.com")))],
        attachments=[Attachment(filename="path")])


    print("Exchange Logged_in: ",exchange.logged_in)
    #exchange.login("praxisprojekt-remail@uni-due.de",keyring.get_password("remail/exchange","praxisprojekt-remail@uni-due.de"))
    print("Exchange Logged_in: ",exchange.logged_in)
    emails = exchange.get_emails()
    #exchange.send_email(test)
    exchange.logout()
    print("Exchange Logged_in: ",exchange.logged_in)

def create_email(uid : str,sender : str, subject: str, body: str, attachments: list[str], to_recipients: list[str],cc_recipients: list[str],bcc_recipients: list[str], html_files: list[str] = None ) -> Email:
    
    sender_contact = get_contact(sender)

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
        recipients=recipients
    )

def get_contact(email : str) -> Contact:
    return Contact(email_address=email)

if __name__ == "__main__":
    print("Starte Tests")
    imap_test()
    #exchange_test()
    print("Tests beendet")
    
    

