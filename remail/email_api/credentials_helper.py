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
    return os.environ.get("EMAIL"+_protocol)

def get_password():
    return os.environ.get("PASSWORD"+_protocol)

def get_username():
    return os.environ.get("USERNAME"+_protocol)

def get_host():
    return os.environ.get("HOST"+_protocol)