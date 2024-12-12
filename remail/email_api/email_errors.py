class EmailError(Exception):
    """base class for remail exceptions"""
    pass

class InvalidEmail(EmailError):
    """email address in Credentials is invalid. Only raised in exchange"""
    pass

class InvalidLoginData(EmailError):
    pass

class NotLoggedIn(EmailError):
    pass

class UnknownError(EmailError):
    pass

class RecipientsFail(EmailError):
    pass

class ServerConnectionFail(EmailError):
    pass

class SMTPSenderFalse(EmailError):
    pass

class SMTPDataFalse(EmailError):
    pass

class CommandNotSupported(EmailError):
    pass