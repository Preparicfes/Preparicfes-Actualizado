

"""
🗄️ CONFIGURACIÓN DE BASE DE DATOS - HERRAMIENTA PEDAGÓGICA

Este archivo configura la conexión a la base de datos SQLite.
SQLAlchemy es una biblioteca que facilita trabajar con bases de datos.

📚 CONCEPTOS PARA APRENDER:
- Motor (Engine): La conexión principal a la base de datos
- Sesión: Una "conversación" temporal con la base de datos
- ORM: Object-Relational Mapping (traduce objetos Python a tablas SQL)
- Dependencias: FastAPI puede "inyectar" automáticamente la sesión de BD

📚 ¿POR QUÉ USAMOS SESIONES?
- Agrupan múltiples operaciones de base de datos
- Permiten hacer "rollback" si algo sale mal
- Mejoran el rendimiento al reutilizar conexiones
"""

import os 
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# --- Configuración de la Base de Datos ---

load_dotenv()
URL_DATABASE= os.getenv("URL_DATABASE")

if not URL_DATABASE: 
    raise ValueError(
        "URL_DATABASE No esta configurado"
    )
engine= create_engine(URL_DATABASE)

# Creamos una "fábrica" de sesiones llamada SessionLocal.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --- Dependencia de FastAPI para la Sesión ---

def get_db():
    """
    Función generadora que proporciona sesiones de base de datos.
    FastAPI la usa automáticamente cuando ve SessionDepends.
    """
    with SessionLocal() as session:
        yield session

# Dependencia que FastAPI puede inyectar automáticamente
SessionDepends = Annotated[Session, Depends(get_db)]