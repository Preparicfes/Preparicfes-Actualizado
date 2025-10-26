import os 
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Conexión a base de datos
load_dotenv()
DB_URL = os.getenv("URL_DATABASE")

if not DB_URL: 
    raise ValueError("URL_DATABASE no configurada")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para FastAPI
def get_db():
    with SessionLocal() as session:
        yield session

SessionDepends = Annotated[Session, Depends(get_db)]