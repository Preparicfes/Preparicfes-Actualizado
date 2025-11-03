import os
import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def hash_password(password: str) -> str:
    """Encripta contraseña con SHA-256 y salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(plain: str, hashed: str) -> bool:
    """Verifica contraseña"""
    try:
        salt, pwd_hash = hashed.split(":")
        return hashlib.sha256(f"{plain}{salt}".encode()).hexdigest() == pwd_hash
    except:
        return False

def crear_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crea JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=480))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str) -> dict | None:
    """Decodifica JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if (user_id := payload.get("user_id")) and (grado := payload.get("grado")):
            return {"user_id": user_id, "grado": grado}
    except JWTError:
        pass
    return None

def obtener_usuario_actual(request: Request) -> dict | None:
    """Obtiene usuario del token en cookies"""
    if token := request.cookies.get("access_token"):
        return verificar_token(token)
    return None

def requerir_autenticacion(request: Request) -> dict:
    """Valida autenticación o redirige"""
    if not (usuario := obtener_usuario_actual(request)):
        raise HTTPException(status_code=303, detail="No autenticado", headers={"Location": "/"})
    return usuario