from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def crear_token(data: dict, expires_delta: timedelta = None):
    """Crea un token JWT con los datos del usuario"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=480)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verificar_token(token: str):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        grado: str = payload.get("grado")
        
        if user_id is None or grado is None:
            return None
        
        return {"user_id": user_id, "grado": grado}
    except JWTError:
        return None

def obtener_usuario_actual(request: Request):
    """Obtiene el usuario del token guardado en las cookies"""
    token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    return verificar_token(token)

def requerir_autenticacion(request: Request):
    """
    Verifica que el usuario esté autenticado.
    Si no lo está, lanza una excepción HTTP que será manejada por FastAPI.
    """
    usuario = obtener_usuario_actual(request)
    
    if not usuario:
        # Lanzar una excepción que FastAPI manejará correctamente
        raise HTTPException(
            status_code=303,
            detail="No autenticado",
            headers={"Location": "/"}
        )
    
    return usuario