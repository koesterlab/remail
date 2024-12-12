class InvalidEmail(Exception):
    pass

class InvalidLoginData(Exception):
    pass

class NotLoggedIn(Exception):
    pass

class UnknownError(Exception):
    pass

class SMTPAuthenticationFalse(Exception):
    pass

class SMTPRecipientsFalse(Exception):
    pass

class SMTPServerConnectionFalse(Exception):
    pass

class SMTPSenderFalse(Exception):
    pass

class SMTPDataFalse(Exception):
    pass

class SMTPNotSupported(Exception):
    pass