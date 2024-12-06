from enum import Enum

class Protocol(Enum):
    IMAP = 0,
    EXCHANGE = 1

_protocol = Protocol.IMAP

@property
def protocol():
    return _protocol

@protocol.setter
def protocol(value):
    global _protocol
    _protocol = value

def get_email():
    pass

def get_password():
    pass

def get_username():
    pass