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

class SMTPAuthenticationFalse(EmailError):
    pass

class SMTPRecipientsFalse(EmailError):
    pass

class SMTPServerConnectionFalse(EmailError):
    pass

class SMTPSenderFalse(EmailError):
    pass

class SMTPDataFalse(EmailError):
    pass

class SMTPNotSupported(EmailError):
    pass