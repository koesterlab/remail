from abc import ABC, abstractmethod
from remail.email_api.object import Email, EmailReception, Attachment, Contact, RecipientKind
from imapclient import IMAPClient
from smtplib import SMTP_SSL,SMTP_SSL_PORT, SMTPAuthenticationError,SMTPRecipientsRefused,SMTPServerDisconnected,SMTPDataError,SMTPConnectError,SMTPHeloError,SMTPNotSupportedError
import email
from imapclient.exceptions import LoginError,IMAPClientAbortError,IMAPClientError,CapabilityError
from email.message import EmailMessage
from datetime import datetime
from exchangelib import Credentials, Account, Message, FileAttachment, EWSDateTime, UTC, errors as exch_errors
import os
import keyring
from bs4 import BeautifulSoup
import mimetypes
from werkzeug.utils import secure_filename
import tempfile
from email.header import decode_header
from email.utils import parsedate_to_datetime
from tzlocal import get_localzone
import remail.email_api.credentials_helper as ch
import remail.email_api.email_errors as ee

def error_handler(func):
    
    def wrapper(self, *args, **kwargs):

        RECIPIENTSFAIL = (SMTPRecipientsRefused, exch_errors.ErrorInvalidRecipients)
        CONNECTIONFAIL = (SMTPConnectError, exch_errors.ErrorConnectionFailed, exch_errors.TransportError, SMTPServerDisconnected,SMTPHeloError,IMAPClientError,IMAPClientAbortError,CapabilityError)
        INVALIDLOGINDATA = (exch_errors.UnauthorizedError, LoginError,SMTPAuthenticationError)

        try:
            return func(self, *args, **kwargs)
        except ee.EmailError as e:
            raise e
        except ValueError as e:
            if "is not an email address" in str(e):
                raise ee.InvalidLoginData() from None
            else:
                raise ee.UnknownError(f"An unexpected error occurred: {str(e)}") from e
        except INVALIDLOGINDATA:
            raise ee.InvalidLoginData() from None
        except SMTPNotSupportedError:
            raise ee.CommandNotSupported() from None
        except CONNECTIONFAIL:
            raise ee.ServerConnectionFail() from None
        except SMTPDataError:
            raise ee.SMTPDataFalse() from None
        except RECIPIENTSFAIL:
            raise ee.RecipientsFail() from None
        except Exception as e:
            raise ee.UnknownError(f"An unexpected error occurred: {str(e)}") from e
    return wrapper


class ProtocolTemplate(ABC):
    
    @property
    @abstractmethod
    def logged_in(self) -> bool:
        """returns true if user is logged in otherwise false"""
        pass
    
    @abstractmethod
    def login(self) -> bool:
        """logs in user with password and username/email """
        pass

    @abstractmethod
    def logout(self):
        """logs out the user"""
        pass

    @abstractmethod
    def send_email(self,email: Email):
        """sends the given email"""
        pass

    @abstractmethod
    def get_deleted_emails(self, uids: list[str]) -> list[str]:
        """returns a list of the message ids, that still exist in the database but don't
        exist on the server anymore"""
        pass

    @abstractmethod
    def mark_email(self, message_id: str, read: bool):
        """Marks the email with given message_id as read(True)/unread(False)"""
        pass

    @abstractmethod
    def delete_email(self, message_id: str):
        """Deletes the email with given message_id"""
        pass

    @abstractmethod
    def get_emails(self, date: datetime = None)->list[Email]:
        """Returns a list of email objects later than the datetime.
        If no datetime is passed, it returns all emails"""
        pass

class ImapProtocol(ProtocolTemplate):
    
    #email address
    user_username = None
    #or imappassword
    user_password = None
    host = ch.get_host()
    def __init__(self):
        self.IMAP = IMAPClient(self.host,use_uid=True)
        

    SMTP_HOST = host

    @property
    def logged_in(self) -> bool:
        return self.user_password is not None and self.user_username is not None
    
    def login(self):
        if self.logged_in: 
            return
        try:
            self.user_username = ch.get_email()
            self.user_password = ch.get_password()
            self.IMAP.login(self.user_username, self.user_password)
        except LoginError:
            raise ee.InvalidLoginData() from None
        except Exception as e:
            raise e


    def logout(self):
        self.IMAP.logout()
        self.user_password = None
        self.user_username = None

        
    @error_handler
    def send_email(self, email:Email):
        if not self.logged_in:
            raise ee.NotLoggedIn()

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
                raise FileNotFoundError()
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
        
    @error_handler
    def delete_email(self, message_id:str):
        """Requierment: User is logged in"""
        if not self.logged_in: 
            raise ee.NotLoggedIn()
        folder_names = [folder[2] for folder in self.IMAP.list_folders()]
        for mailbox in folder_names:
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(['HEADER', 'Message-ID', message_id])
            if messages_ids:
                    self.IMAP.delete_messages(messages_ids)
                    self.IMAP.expunge()
            
    @error_handler
    def get_emails(self, date : datetime = None)->list[Email]:
        if not self.logged_in: 
            raise ee.NotLoggedIn()
        listofMails = []
        folder_names = [folder[2] for folder in self.IMAP.list_folders()]
        for mailbox in folder_names:
            listofMails.append(self._get_emails(mailbox,date))
        return listofMails
    
    @error_handler
    def _get_emails(self, folder : str, date : datetime = None)-> list[Email]:
        listofMails = []
        try:
            self.IMAP.select_folder(folder)
            if date is not None:
                messages_ids = self.IMAP.search([u'SINCE', date])
            else: 
                messages_ids = self.IMAP.search(["ALL"])

            for _,message_data in self.IMAP.fetch(messages_ids,["RFC822"]).items():
                email_message = email.message_from_bytes(message_data[b"RFC822"])

                if date is not None and date > parsedate_to_datetime(email_message["Date"]): 
                    continue
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
                                file, encoding = decode_header(filename)[0]
                                if isinstance(file, bytes):
                                    filename = file.decode(encoding or "utf-8",errors="replace")
                                    attachments_file_names += [safe_file(filename,part.get_payload(decode=True))]
                                    
                        #get HTML parts
                        if part.get_content_disposition() == "text/html":
                            html_content = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8",errors="replace")
                            html_parts.append(html_content)

                        #get plain text from email
                        if ctype == 'text/plain' and 'attachment' not in cdispo:
                            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8",errors="replace")

                #get plain if no multipart
                else:
                    body = email_message.get_payload(decode=True).decode(email_message.get_content_charset() or "utf-8",errors="replace")

                listofMails += [create_email(
                                    uid = email_message["Message-Id"],
                                    sender = email_message["From"],
                                    subject = email_message["Subject"],
                                    body = body,
                                    attachments = attachments_file_names,
                                    to_recipients = email_message["To"],
                                    cc_recipients = email_message["Cc"],
                                    bcc_recipients = email_message["Bcc"],
                                    date =  parsedate_to_datetime(email_message["Date"]),
                                    html_files = html_parts)]
        except Exception as e:
            raise e
        finally:
            self.IMAP.close_folder(folder)
        return listofMails

    @error_handler
    def get_deleted_emails(self,message_ids:list[str])->list[str]:
        if not self.logged_in: 
            raise ee.NotLoggedIn()
        listofUIPsIMAP = []
        for mailbox in [folder[2] for folder in self.IMAP.list_folders()]:
            self.IMAP.select_folder(mailbox)
            list_messages_ids = self.IMAP.search(["ALL"])
            for _,message_data in self.IMAP.fetch(list_messages_ids,["RFC822"]).items():
                email_message = email.message_from_bytes(message_data[b"RFC822"])
                listofUIPsIMAP.append(email_message["Message-Id"])
            self.IMAP.close_folder(mailbox)
        return list(set(message_ids)-set(listofUIPsIMAP))
    
    @error_handler
    def mark_email(self,message_id:str,read:bool):
        if not self.logged_in: 
           raise ee.NotLoggedIn()
        if read:
            self.IMAP.add_flags(message_id,["SEEN"])
        else:
            self.IMAP.remove_flags(message_id,["SEEN"])



class ExchangeProtocol(ProtocolTemplate):
    

    def __init__(self):
        self.cred = None
        self.acc = None
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @error_handler
    def login(self):
        
        if self.logged_in:
            return

        user = ch.get_email()
        password = ch.get_password()
        username = ch.get_username()

        
        self.cred = Credentials(username,password)
        self.acc = Account(user, credentials=self.cred, autodiscover=True)
        self._logged_in = True
        
    
    def logout(self):
        self.acc = None
        self.cred = None
        self._logged_in = False
    
    @error_handler
    def send_email(self,email:Email):
        """Requierment: User is logged in"""
        if not self.logged_in:
            raise ee.NotLoggedIn()
        

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

    @error_handler
    def mark_email(self, message_id: str, read : bool):
        if not self.logged_in:
            raise ee.NotLoggedIn()
        
        for item in self.acc.inbox.filter(message_id=message_id):
            item.is_read = read
            item.save(update_fields = ["is_read"])

    @error_handler
    def delete_email(self, message_id:str):
        """Requierment: User is logged in
        moves the email in the trash folder"""
        if not self.logged_in:
            raise ee.NotLoggedIn()
        
        for item in self.acc.inbox.filter(message_id=message_id):
            item.move_to_trash()
        
    @error_handler
    def get_deleted_emails(self, message_ids : list[str]) -> list[str]:
        if not self.logged_in:
            raise ee.NotLoggedIn()
        
        server_uids = [item.message_id for item in self.acc.inbox.all()]

        return list(set(message_ids) - set(server_uids))

    @error_handler
    def get_emails(self, date : datetime = None)->list[Email]:
        
        if not self.logged_in:
            raise ee.NotLoggedIn()

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
    @error_handler
    def _get_email_exchange(self, item):
        attachments = []
        for attachment in item.attachments:
            if isinstance(attachment, FileAttachment):
                attachments += [safe_file(attachment.name,attachment.content)]
        
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
                cc_recipients=item.cc_recipients if item.cc_recipients else [],
                bcc_recipients=item.bcc_recipients if item.bcc_recipients else [],
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
        message_id=uid,
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

def safe_file(filename:str,content:bytes)->str:
    max_size = 10*1024*1024 # muss noch von wo anders bestimmt werden
    if len(content) > max_size:
        raise BufferError
    temp_dir = tempfile.gettempdir()
    safe_filename = secure_filename(filename)
    filepath = os.path.join(temp_dir,safe_filename)
    try:
        with open(filepath,"wb") as f:
            f.write(content)
        return filepath
    except Exception as e:
        raise e


if __name__ == "__main__":
    imap = ImapProtocol()
    imap.login()
    imap.get_emails(datetime(2024,12,6,19,0,0,tzinfo=get_localzone()))
    imap.get_emails()
    imap.logout()