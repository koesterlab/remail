from enum import Enum
import keyring
import os


class Protocol(str, Enum):
    IMAP = ("IMAP",)
    EXCHANGE = "EXCHANGE"


protocol = Protocol.IMAP


def get_email():
    """returns the email address of the Imap or Exchange user"""
    email = os.environ.get("EMAIL" + protocol)
    if email:
        return email
    if protocol == Protocol.IMAP:
        return "thatchmilo35@gmail.com"
    else:
        return "praxisprojekt-remail@uni-due.de"


def get_password():
    """returns the password of the user"""
    password = os.environ.get("PASSWORD" + protocol)
    if password:
        return password
    password = keyring.get_password("remail/" + protocol, get_email())
    if password:
        return password
    return ""
    # password = getpass("Gebe das "+ protocol+"-Passwort ein, um es auf deinem Rechner zu hinterlegen: ")
    # keyring.set_password("remail/"+protocol,"praxisprojekt-remail@uni-due.de",password)


def get_username():
    """returns the username of the user"""
    username = os.environ.get("REMAIL_USERNAME")
    if username:
        return username
    return "ude-1729267167"


def get_host():
    """returns the Imap host address"""
    host = os.environ.get("REMAIL_HOST")
    if host:
        return host
    return "imap.gmail.com"
