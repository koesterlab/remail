from sqlmodel import SQLModel, create_engine
from remail.database.models import Email, Contact, EmailReception, RecipientKind, Attachment, User

def init_db():
    engine = create_engine("duckdb:///database.db")
    SQLModel.metadata.create_all(engine)
