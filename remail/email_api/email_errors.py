class InvalidEmail(Exception):
    pass

class InvalidLoginData(Exception):
    pass

class NotLoggedIn(Exception):
    pass

class SMTPAuthenticationFalse(Exception):
    pass

class SMTPRecipientsFalse(Exception):
    pass

class SMTPServerDisconnect(Exception):
    pass