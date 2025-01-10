from remail.email_api.service import ExchangeProtocol
from remail.database.models import Email, EmailReception, Contact, RecipientKind
import remail.email_api.credentials_helper as ch
from datetime import datetime
from tzlocal import get_localzone
import random

subjects = [
    "Welcome to our service!",
    "Your invoice is ready",
    "Important security update",
    "Special offer just for you",
    "Meeting reminder",
    "Thank you for your purchase",
    "Last chance to save big!",
    "Update your account details",
    "New features added to your account",
    "Feedback request",
]

bodies = [
    "Hello, we are excited to welcome you to our platform. Let us know if you need any help getting started.",
    "Your invoice for this month is now ready. Please log in to your account to view it.",
    "Please update your password to ensure your account remains secure.",
    "We have an exclusive offer just for you. Don't miss out!",
    "This is a reminder for your meeting scheduled on Monday at 10:00 AM.",
    "Thank you for your recent purchase! We hope you enjoy your new item.",
    "Hurry! This is your last chance to save 50% on all items in our store.",
    "Please update your account details to avoid service interruptions.",
    "We've added new features to your account. Check them out today!",
    "We value your feedback. Please take a moment to complete our survey.",
]

ch.protocol = ch.Protocol.EXCHANGE
ex = ExchangeProtocol(ch.get_email(), ch.get_password(), ch.get_username())

ex.login()
m = Email(
    subject=random.choice(subjects),
    body=random.choice(bodies),
    recipients=[
        EmailReception(
            contact=(Contact(email_address="thatchmilo35@gmail.com")),
            kind=RecipientKind.to,
        )
    ],
)
print(ex.get_emails(date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=get_localzone())))
