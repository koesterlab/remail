from enum import Enum
import keyring
from getpass import getpass
import os

class Protocol(str,Enum):
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
    email = os.environ.get("EMAIL"+_protocol)
    if email:
        return email
    if _protocol == Protocol.IMAP:
        return "thatchmilo35@gmail.com"
    else:
        return "praxisprojekt-remail@uni-due.de"

def get_password():
    password = os.environ.get("PASSWORD"+_protocol)
    if password:
        return password
    password = keyring.get_password("remail/"+_protocol,"praxisprojekt-remail@uni-due.de")
    if password:
        return password
    password = getpass("Gebe das "+ _protocol+"-Passwort ein, um es auf deinem Rechner zu hinterlegen: ")
    keyring.set_password("remail/"+_protocol,"praxisprojekt-remail@uni-due.de",password)

def get_username():
    username = os.environ.get("REMAIL_USERNAME")
    if username:
        return username
    return "ude-1729267167"

def get_host():
    host = os.environ.get("REMAIL_HOST")
    if host:
        return host
    return "imap.gmail.com"