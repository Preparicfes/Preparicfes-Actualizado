import os
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

if not (DB_URL := os.getenv("URL_DATABASE")):
    raise ValueError("URL_DATABASE no configurada")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    with SessionLocal() as session:
        yield session

SessionDepends = Annotated[Session, Depends(get_db)]