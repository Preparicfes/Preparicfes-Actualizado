"""
Script para actualizar las contraseñas existentes en la base de datos.
Ejecutar UNA SOLA VEZ después de instalar las nuevas dependencias.
"""
from passlib.context import CryptContext
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_engine(os.getenv("URL_DATABASE"))

print("🔐 Actualizando contraseñas...")

with engine.connect() as conn:
    # Obtener todos los usuarios
    usuarios = conn.execute(text("SELECT id, password FROM usuarios")).fetchall()
    
    actualizados = 0
    for user_id, password in usuarios:
        # Si la contraseña no está encriptada (no empieza con $2b$)
        if not password.startswith("$2b$"):
            password_encriptada = pwd_context.hash(password)
            conn.execute(
                text("UPDATE usuarios SET password = :pass WHERE id = :id"),
                {"pass": password_encriptada, "id": user_id}
            )
            actualizados += 1
    
    conn.commit()
    print(f"✅ {actualizados} contraseñas actualizadas correctamente")