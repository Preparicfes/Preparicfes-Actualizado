from sqlalchemy import create_engine, text
import hashlib
import secrets
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("URL_DATABASE"))

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

print("🔐 Actualizando contraseñas...")

# IMPORTANTE: Cambia estos datos por tus usuarios reales
usuarios_actualizar = [
    {"email": "tu@email.com", "password_original": "tucontraseña123"},
    # Agrega más usuarios aquí si tienes
]

with engine.connect() as conn:
    for user_data in usuarios_actualizar:
        email = user_data["email"]
        password_nueva = hash_password(user_data["password_original"])
        
        conn.execute(
            text("UPDATE usuarios SET password = :pass WHERE email = :email"),
            {"pass": password_nueva, "email": email}
        )
        print(f"✅ Actualizado: {email}")
    
    conn.commit()
    print("\n✅ Todas las contraseñas actualizadas correctamente")