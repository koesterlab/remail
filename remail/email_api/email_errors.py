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
    """Recipients not accepted"""
    pass

class ServerConnectionFail(EmailError):
    """server connection unexpectedly fails, or attempt to use instance without connection"""
    pass

class SMTPSenderFalse(EmailError):
    """Sender refused"""
    pass

class SMTPDataFalse(EmailError):
    pass

class CommandNotSupported(EmailError):
    """command is not supported by the server"""
    pass