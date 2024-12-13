class EmailError(Exception):
    """base class for remail exceptions"""
    pass

class InvalidLoginData(EmailError):
    """Login Data is wrong (email or password)"""
    pass

class NotLoggedIn(EmailError):
    """User is not logged in"""
    pass

class UnknownError(EmailError):
    """Exception raised is not handled yet"""
    pass

class RecipientsFail(EmailError):
    """Recipients not accepted"""
    pass

class ServerConnectionFail(EmailError):
    """server connection unexpectedly fails, or attempt to use instance without connection"""
    pass

class SMTPDataFalse(EmailError):
    """Server replied with an unexpected error code (other than a refusal of a recipient)"""
    pass
