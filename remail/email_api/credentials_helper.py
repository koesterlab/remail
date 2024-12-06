from enum import StrEnum
import os

class Protocol(StrEnum):
    IMAP = "IMAP",
    EXCHANGE = "EXCHANGE"

_protocol = Protocol.IMAP

@property
def protocol():
    return _protocol

@protocol.setter
def protocol(value):
    global _protocol
    _protocol = value

def get_email():
    return os.environ.get("email"+_protocol)

def get_password():
    return os.environ.get("password"+_protocol)

def get_username():
    return os.environ.get("username"+_protocol)