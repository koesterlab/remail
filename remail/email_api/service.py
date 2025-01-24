from abc import ABC, abstractmethod
from remail.database.models import (
    Email,
    EmailReception,
    Attachment,
    RecipientKind,
)
from imapclient import IMAPClient
from smtplib import (
    SMTP_SSL,
    SMTP_SSL_PORT,
    SMTPAuthenticationError,
    SMTPRecipientsRefused,
    SMTPServerDisconnected,
    SMTPDataError,
    SMTPConnectError,
    SMTPHeloError,
)
import email
from imapclient.exceptions import (
    LoginError,
    IMAPClientAbortError,
    IMAPClientError,
    CapabilityError,
)
from email.message import EmailMessage
from datetime import datetime
from exchangelib import (
    Credentials,
    Account,
    Message,
    FileAttachment,
    errors as exch_errors,
    FolderCollection,
    UTC,
)
import os
import mimetypes
from werkzeug.utils import secure_filename
import tempfile
from email.header import decode_header
from email.utils import parsedate_to_datetime, getaddresses
import remail.email_api.email_errors as ee
from pytz import timezone


def error_handler(func):
    def wrapper(self, *args, **kwargs):
        RECIPIENTSFAIL = (SMTPRecipientsRefused, exch_errors.ErrorInvalidRecipients)
        CONNECTIONFAIL = (
            SMTPConnectError,
            exch_errors.ErrorConnectionFailed,
            exch_errors.TransportError,
            SMTPServerDisconnected,
            SMTPHeloError,
            IMAPClientError,
            IMAPClientAbortError,
            CapabilityError,
        )
        INVALIDLOGINDATA = (
            exch_errors.UnauthorizedError,
            LoginError,
            SMTPAuthenticationError,
        )

        try:
            return func(self, *args, **kwargs)
        except ee.EmailError as e:
            raise e
        except ValueError as e:
            if "is not an email address" in str(e):
                raise ee.InvalidLoginData()
            else:
                raise ee.UnknownError(f"An unexpected error occurred: {str(e)}") from e
        except INVALIDLOGINDATA:
            raise ee.InvalidLoginData()
        except CONNECTIONFAIL:
            raise ee.ServerConnectionFail()
        except SMTPDataError:
            raise ee.SMTPDataFalse()
        except RECIPIENTSFAIL:
            raise ee.RecipientsFail()
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
    def login(self):
        """logs in user with password and username/email"""
        pass

    @abstractmethod
    def logout(self):
        """logs out the user"""
        pass

    @abstractmethod
    def send_email(self, email: Email):
        """sends the given email"""
        pass

    @abstractmethod
    def get_deleted_emails(self, message_ids: list[str]) -> list[str]:
        """returns a list of the message ids, that still exist in the database but don't
        exist on the server anymore"""
        pass

    @abstractmethod
    def mark_email(self, message_id: str, read: bool):
        """Marks the email with given message_id as read(True)/unread(False)"""
        pass

    @abstractmethod
    def delete_email(self, message_id: str, hard_delete: bool = False):
        """Deletes the email with given message_id
        hard_delete = True -> completely removes email
        hard_delete = False -> moves to trash folder"""
        pass

    @abstractmethod
    def get_emails(self, date: datetime = None) -> list[Email]:
        """Returns a list of email objects later than the datetime.
        If no datetime is passed, it returns all emails
        tzinfo is mandatory in datetime:
            eg: datetime(2024,12,13,10,0,0,tzinfo=tzlocal.get_localzone())
            ->import: tzlocal"""
        pass


class ImapProtocol(ProtocolTemplate):
    def __init__(
        self, email: str, password: str, host: str, controller: "EmailController"
    ):  # type: ignore
        self.user_username = email
        self.user_password = password
        self.host = host
        self._logged_in = False
        self.IMAP = IMAPClient(self.host, use_uid=True)
        self.controller = controller

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @error_handler
    def login(self):
        if self.logged_in:
            return
        if self.user_password is None:
            raise ee.InvalidLoginData() from None
        try:
            self.IMAP.login(self.user_username, self.user_password)
            self._logged_in = True
        except LoginError:
            raise ee.InvalidLoginData() from None
        except Exception as e:
            raise e

    @error_handler
    def logout(self):
        self.IMAP.logout()
        self.user_password = None
        self.user_username = None
        self._logged_in = False

    @error_handler
    def send_email(self, email: Email):
        if not self.logged_in:
            raise ee.NotLoggedIn()

        SMTP_USER = self.user_username
        SMTP_PASS = self.user_password

        to = []
        cc = []
        bcc = []
        for recipent in email.recipients:
            match recipent.kind:
                case RecipientKind.to:
                    to += [recipent.contact.email_address]
                case RecipientKind.cc:
                    cc += [recipent.contact.email_address]
                case RecipientKind.bcc:
                    bcc += [recipent.contact.email_address]

        # craft email
        from_email = SMTP_USER
        msg = EmailMessage()
        msg["Subject"] = email.subject
        msg["From"] = from_email
        msg["To"] = to
        msg["Cc"] = cc
        if len(bcc) > 0:
            msg["Bcc"] = ",".join(bcc)
        msg.set_content(email.body)

        # attachment
        for att in email.attachments:
            filename = os.path.basename(att.filename)  # Sanitize filename
            if not os.path.exists(att.filename) or not os.path.isfile(att.filename):
                raise FileNotFoundError()
            with open(os.path.abspath(att.filename), "rb") as file:
                file_data = file.read()
                type = mimetypes.guess_type(file.name)[0].split("/")
                main_type = type[0]
                sub_type = type[1]
            msg.add_attachment(
                file_data, maintype=main_type, subtype=sub_type, filename=filename
            )

        # connect/authenticate
        smtp_server = SMTP_SSL(self.host, port=SMTP_SSL_PORT)
        smtp_server.login(SMTP_USER, SMTP_PASS)
        smtp_server.send_message(msg)

        # disconnect
        smtp_server.quit()

    @error_handler
    def delete_email(self, message_id: str, hard_delete: bool):
        if not self.logged_in:
            raise ee.NotLoggedIn()
        # gets all accessable folder names from the connection
        folder_names = self._get_folder_names()
        for mailbox in folder_names:
            # searches through all folders for the message_id
            self.IMAP.select_folder(mailbox)
            messages_ids = self.IMAP.search(["HEADER", "Message-ID", message_id])
            if messages_ids:
                if hard_delete:
                    # deletes the email completely
                    self.IMAP.delete_messages(messages_ids)
                    self.IMAP.expunge()
                else:
                    # only moves email to Trash folder
                    folder_name = self._get_folder_name_with_flags([b"\\Trash"])
                    self.IMAP.move(messages_ids, folder_name[0])

    @error_handler
    def get_emails(self, date: datetime = None) -> list[Email]:
        if not self.logged_in:
            raise ee.NotLoggedIn()
        listofMails = []
        folder_names = self._get_folder_names()
        for mailbox in folder_names:
            # goes through all email folders and sums its content
            listofMails += self._get_emails(mailbox, date)
        return listofMails

    @error_handler
    def _get_emails(self, folder: str, date: datetime = None) -> list[Email]:
        listofMails = []
        try:
            self.IMAP.select_folder(folder)
            if date is not None:
                # if date time is given filter all emails after this date
                messages_ids = self.IMAP.search(["SINCE", date])
                date = date.astimezone(timezone("UTC"))
            else:
                # no date time given: return all emails
                messages_ids = self.IMAP.search(["ALL"])
            for _, message_data in self.IMAP.fetch(messages_ids, ["RFC822"]).items():
                email_message = email.message_from_bytes(message_data[b"RFC822"])
                if date is not None and date > parsedate_to_datetime(
                    email_message["Date"]
                ).astimezone(timezone("UTC")):
                    continue
                attachments_file_names = []
                html_parts = []
                body = None
                if email_message.is_multipart():
                    # iter over all parts
                    for part in email_message.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get("Content-Disposition"))

                        # get attachments part
                        if part.get_content_disposition() == "attachment":
                            filename = part.get_filename()
                            # safe attachments
                            if filename:
                                file, encoding = decode_header(filename)[0]
                                if isinstance(file, bytes):
                                    filename = file.decode(
                                        encoding or "utf-8", errors="replace"
                                    )
                                    attachments_file_names += [
                                        safe_file(
                                            filename, part.get_payload(decode=True)
                                        )
                                    ]

                        # get HTML parts
                        if part.get_content_type() == "text/html":
                            html_content = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", errors="replace"
                            )
                            html_parts.append(html_content)

                        # get plain text from email
                        if ctype == "text/plain" and "attachment" not in cdispo:
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", errors="replace"
                            )

                # get plain if no multipart
                else:
                    body = email_message.get_payload(decode=True).decode(
                        email_message.get_content_charset() or "utf-8", errors="replace"
                    )

                x = getaddresses([email_message["From"]])
                saddr = x[0][1]
                listofMails += [
                    create_email(
                        uid=email_message["Message-Id"],
                        sender=saddr,
                        subject=email_message["Subject"],
                        body=body,
                        attachments=attachments_file_names,
                        to_recipients=[
                            (name,addr)
                            for name, addr in getaddresses([email_message["To"]])
                            if addr and addr.lower() != "none"
                        ],
                        cc_recipients=[
                            (name,addr)
                            for name, addr in getaddresses([email_message["Cc"]])
                            if addr and addr.lower() != "none"
                        ],
                        bcc_recipients=[
                            (name,addr)
                            for name, addr in getaddresses([email_message["Bcc"]])
                            if addr and addr.lower() != "none"
                        ],
                        date=parsedate_to_datetime(email_message["Date"]).astimezone(
                            timezone("UTC")
                        ),
                        controller=self.controller,
                        html_files=html_parts,
                    )
                ]
        except Exception as e:
            raise e
        finally:
            self.IMAP.close_folder()
        return listofMails

    @error_handler
    def get_deleted_emails(self, message_ids: list[str]) -> list[str]:
        if not self.logged_in:
            raise ee.NotLoggedIn()
        listofUIPsIMAP = []
        folder_names = self._get_folder_names()
        for mailbox in folder_names:
            # iterates over all available folders
            self.IMAP.select_folder(mailbox)
            list_messages_ids = self.IMAP.search(["ALL"])
            # gets all message ids from the connection
            for _, message_data in self.IMAP.fetch(
                list_messages_ids, ["RFC822"]
            ).items():
                email_message = email.message_from_bytes(message_data[b"RFC822"])
                listofUIPsIMAP.append(email_message["Message-Id"])
            self.IMAP.close_folder()
        # given ids without the ids, that are currently on the connection
        return list(set(message_ids) - set(listofUIPsIMAP))

    @error_handler
    def mark_email(self, message_id: str, read: bool):
        if not self.logged_in:
            raise ee.NotLoggedIn()
        if read:
            # mark email as seen
            self.IMAP.add_flags(message_id, ["SEEN"])
        else:
            # mark email as unseen
            self.IMAP.remove_flags(message_id, ["SEEN"])

    @error_handler
    def _get_folder_names(self) -> list[str]:
        """returns a list with all available folder names"""
        all_folder_names = self.IMAP.list_folders()
        all_folders_filterd = []
        baned_flags = (
            b"\\HasChildren",
            b"\\Drafts",
            b"\\Junk",
            b"\\Noselect",
            b"\\All",
            b"\\Trash",
        )
        for folder in all_folder_names:
            # adds only valid folders to the result
            if not (set(folder[0]) & set(baned_flags)):
                all_folders_filterd.append(folder[2])
        return all_folders_filterd

    @error_handler
    def _get_folder_name_with_flags(
        self, flags: list[bytes], need_of_all_flags: bool = False
    ) -> list[str]:
        """returns a list with all available folder names including the flags"""
        all_folder_names = self.IMAP.list_folders()
        all_folders_filtered = []
        for folder in all_folder_names:
            # iterates over all folder names in the connection
            disjunktion = set(folder[0]) & set(flags)
            if disjunktion:
                if need_of_all_flags:
                    # if all flags are required, checks if the folder has all of them: adds it to the result
                    if len(disjunktion) == len(flags):
                        all_folders_filtered.append(folder[2])
                else:
                    # if all flags aren't required, just adds the folder to the result
                    all_folders_filtered.append(folder[2])
        return all_folders_filtered


class ExchangeProtocol(ProtocolTemplate):
    def __init__(
        self, email: str, password: str, username: str, controller: "EmailController"
    ):  # type: ignore
        self.cred = None
        self.acc = None
        self._logged_in = False
        self.email = email
        self.password = password
        self.username = username
        self.controller = controller

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @error_handler
    def login(self):
        if self.logged_in:
            return

        self.cred = Credentials(self.username, self.password)
        self.acc = Account(self.email, credentials=self.cred, autodiscover=True)
        self._logged_in = True

    def logout(self):
        self.acc = None
        self.cred = None
        self._logged_in = False

    @error_handler
    def send_email(self, email: Email):
        if not self.logged_in:
            raise ee.NotLoggedIn()

        to = []
        cc = []
        bcc = []
        for recipent in email.recipients:
            match recipent.kind:
                case RecipientKind.to:
                    to += [recipent.contact.email_address]
                case RecipientKind.cc:
                    cc += [recipent.contact.email_address]
                case RecipientKind.bcc:
                    bcc += [recipent.contact.email_address]

        m = Message(
            account=self.acc,
            subject=email.subject,
            body=email.body,
            to_recipients=to,
            cc_recipients=cc,
            bcc_recipients=bcc,
        )

        for attachement in email.attachments:
            path = attachement.filename
            if not os.path.exists(path):
                continue  # jumps to the next attachment if path doesn't exist
            with open(path, "rb") as f:
                content = f.read()
                att = FileAttachment(name=os.path.basename(path), content=content)
                m.attach(att)

        m.send()

    @error_handler
    def mark_email(self, message_id: str, read: bool):
        if not self.logged_in:
            raise ee.NotLoggedIn()

        for item in self._get_items(message_id=message_id):
            item.is_read = read
            item.save(update_fields=["is_read"])

    @error_handler
    def delete_email(self, message_id: str, hard_delete: bool = False):
        if not self.logged_in:
            raise ee.NotLoggedIn()

        for item in self._get_items(message_id=message_id):
            if hard_delete:
                item.delete()
            else:
                item.move_to_trash()

    @error_handler
    def get_deleted_emails(self, message_ids: list[str]) -> list[str]:
        if not self.logged_in:
            raise ee.NotLoggedIn()

        server_uids = [item.message_id for item in self._get_items()]

        return list(set(message_ids) - set(server_uids))

    def _get_items(self, start_date: datetime = None, message_id=""):
        if start_date:
            start_date = start_date.astimezone(UTC)

        email_folders = [
            f
            for f in self.acc.root.walk()
            if f.CONTAINER_CLASS == "IPF.Note"
            and f not in {self.acc.trash, self.acc.junk, self.acc.drafts}
        ]
        folder_collection = FolderCollection(account=self.acc, folders=email_folders)
        if start_date and message_id:
            generator = folder_collection.filter(
                datetime_received__gte=start_date, message_id=message_id
            )
        elif start_date:
            generator = folder_collection.filter(datetime_received__gte=start_date)
        elif message_id:
            generator = folder_collection.filter(message_id=message_id)
        else:
            generator = folder_collection.all()
        for item in generator:
            if isinstance(item, Message):
                yield item

    @error_handler
    def get_emails(self, date: datetime = None) -> list[Email]:
        if not self.logged_in:
            raise ee.NotLoggedIn()

        result = []
        for item in self._get_items(start_date=date):
            result += self._get_email_exchange(item)
        return result

    @error_handler
    def _get_email_exchange(self, item):
        attachments = []
        for attachment in item.attachments:
            if isinstance(attachment, FileAttachment):
                attachments += [safe_file(attachment.name, attachment.content)]

        ews_datetime_str = item.datetime_received.astimezone()
        parsed_datetime = datetime.fromisoformat(
            ews_datetime_str.ewsformat()
        ).astimezone(timezone("UTC"))
        print(parsed_datetime, datetime.now())

        body = item.text_body
        if item.body != body:
            html = [item.body]
        else:
            html = []

        return [
            create_email(
                uid=item.message_id,
                name=item.sender.name,
                sender=item.sender.email_address,
                subject=item.subject,
                body=body,
                attachments=attachments,
                to_recipients=[(i.name,i.email_address) for i in item.to_recipients],
                cc_recipients=[
                    (item.name,item.email_address)
                    for item in (item.cc_recipients if item.cc_recipients else [])
                ],
                bcc_recipients=[
                    (item.name,item.email_address)
                    for item in (item.bcc_recipients if item.bcc_recipients else [])
                ],
                date=parsed_datetime,
                controller=self.controller,
                html_files=html,
            )
        ]


# -------------------------------------------------


def create_email(
    uid: str,
    sender: str,
    subject: str,
    body: str,
    attachments: list[str],
    to_recipients: list[str],
    cc_recipients: list[str],
    bcc_recipients: list[str],
    date: datetime,
    controller: "EmailController",  # type: ignore
    html_files: list[str] = None,
) -> Email:
    sender_contact = controller.get_contact(sender)
    recipients = [
        EmailReception(contact=controller.get_contact(recipient[1],recipient[0]), kind=RecipientKind.to)
        for recipient in to_recipients
    ]
    if cc_recipients:
        recipients += [
            EmailReception(
                contact=controller.get_contact(recipient[1],recipient[0]), kind=RecipientKind.cc
            )
            for recipient in cc_recipients
        ]
    if bcc_recipients:
        recipients += [
            EmailReception(
                contact=controller.get_contact(recipient[1],recipient[0]), kind=RecipientKind.bcc
            )
            for recipient in bcc_recipients
        ]

    email = Email(
        message_id=uid,
        sender=sender_contact,
        subject=subject,
        body=body,
        recipients=recipients,
        date=date,
    )

    attachments_class = [
        Attachment(filename=filename, email=email) for filename in attachments
    ]

    email.attachments = attachments_class

    return email


def safe_file(filename: str, content: bytes) -> str:
    max_size = 10 * 1024 * 1024  # muss noch von wo anders bestimmt werden 10 MB
    if len(content) > max_size:
        raise BufferError(f"File size exceeds limit of {max_size} bytes")
    temp_dir = tempfile.gettempdir()
    safe_filename = secure_filename(filename)
    if not safe_filename:
        raise ValueError("Invalid filename")
    filepath = os.path.join(temp_dir, safe_filename)
    try:
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath
    except Exception as e:
        raise e
