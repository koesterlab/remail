from enum import Enum
from typing import List, Optional
import sqlalchemy
from sqlmodel import Field, SQLModel, Relationship, create_engine
from controller import EmailController
from datetime import datetime
import duckdb
import logging
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Connect to the DuckDB database (will create a file-based database if it doesn't exist)
conn = duckdb.connect('database.db')

engine = create_engine("duckdb:///database.db")
SQLModel.metadata.create_all(engine)

# Controller initialisieren
email_controller = EmailController(engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Datenbank initialisiert")


def id_field(table_name: str):
    sequence = sqlalchemy.Sequence(f"{table_name}_id_seq")
    return Field(
        default=None,
        primary_key=True,
        sa_column_args=[sequence],
        sa_column_kwargs={"server_default": sequence.next_value()},
    )


class Contact(SQLModel, table=True):
    id: Optional[int] = id_field("contact")
    email_address: str
    name: Optional[str] = None

    receptions: List["EmailReception"] = Relationship(back_populates="contact")
    sent_emails: List["Email"] = Relationship(back_populates="sender")


class RecipientKind(Enum):
    to = "to"
    cc = "cc"
    bcc = "bcc"


class EmailReception(SQLModel, table=True):
    email_id: int = Field(foreign_key="email.id", primary_key=True)
    contact_id: int = Field(foreign_key="contact.id", primary_key=True)
    kind: RecipientKind
    email: "Email" = Relationship(back_populates="recipients")
    contact: "Contact" = Relationship(back_populates="receptions")


class Attachment(SQLModel, table=True):
    id: Optional[int] = id_field("attachment")
    filename: str
    email_id: int = Field(default=None, foreign_key="email.id")
    email: "Email" = Relationship(back_populates="attachments")


class Email(SQLModel, table=True):
    id: Optional[int] = id_field("email")
    message_id: str
    sender_id: int = Field(foreign_key="contact.id")
    sender: Contact = Relationship(back_populates="sent_emails")
    subject: str
    body: str
    attachments: List[Attachment] = Relationship(back_populates="email")
    recipients: List[EmailReception] = Relationship(back_populates="email")
    date: datetime


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)