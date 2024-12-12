class EmailError(Exception):
    pass

class InvalidEmail(EmailError):
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