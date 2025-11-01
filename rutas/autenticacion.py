from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from db import SessionDepends
from datetime import datetime, timedelta
from seguridad.autenticacion import crear_token
import hashlib
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def hash_password(password: str) -> str:
    """Encripta una contraseña usando SHA-256 con salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{pwd_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    try:
        salt, pwd_hash = hashed_password.split(":")
        new_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return new_hash == pwd_hash
    except:
        return False

@router.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/registrate", response_class=HTMLResponse, name="registrate")
async def registrate(request: Request):
    return templates.TemplateResponse("registrate.html", {"request": request})

@router.post("/registrar")
async def registrar(request: Request, email: str = Form(...), password: str = Form(...), 
                   grado: str = Form(...), session: SessionDepends = None):
    try:
        # Verificar si el usuario ya existe
        existe = session.execute(text("SELECT id FROM usuarios WHERE email = :email"), 
                                {"email": email}).fetchone()
        if existe:
            return templates.TemplateResponse("registrate.html", 
                {"request": request, "error": "Este correo ya está registrado"})
        
        # Encriptar la contraseña
        password_encriptada = hash_password(password)
        
        # Crear usuario
        session.execute(text("""
            INSERT INTO usuarios (email, password, grado, fecha_registro)
            VALUES (:email, :password, :grado, :fecha)
        """), {"email": email, "password": password_encriptada, "grado": grado, "fecha": datetime.now()})
        session.commit()
        
        return RedirectResponse(url="/?registro=exitoso", status_code=303)
        
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse("registrate.html", 
            {"request": request, "error": f"Error: {str(e)}"})

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), 
               session: SessionDepends = None):
    try:
        # Buscar usuario
        usuario = session.execute(text("""
            SELECT id, password, grado FROM usuarios WHERE email = :email
        """), {"email": email}).fetchone()
        
        # Verificar contraseña
        if not usuario or not verify_password(password, usuario[1]):
            return templates.TemplateResponse("index.html", 
                {"request": request, "error": "Correo o contraseña incorrectos"})
        
        # Crear token de sesión
        token_sesion = crear_token(
            data={"user_id": usuario[0], "grado": usuario[2]},
            expires_delta=timedelta(minutes=480)
        )
        
        # Redirigir y guardar token en cookie
        response = RedirectResponse(url="/intro", status_code=303)
        response.set_cookie(
            key="access_token",
            value=token_sesion,
            httponly=True,
            max_age=480 * 60,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        print(f"Error en login: {e}")
        return templates.TemplateResponse("index.html", 
            {"request": request, "error": "Error al iniciar sesión"})

@router.get("/cerrar-sesion")
async def cerrar_sesion():
    """Cierra la sesión del usuario"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response