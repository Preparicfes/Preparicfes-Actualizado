from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from db import SessionDepends
from seguridad.autenticacion import requerir_autenticacion, crear_token
from passlib.context import CryptContext
from datetime import timedelta

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/usuario", response_class=HTMLResponse, name="usuario")
async def usuario(request: Request, usuario: dict = Depends(requerir_autenticacion), 
                 session: SessionDepends = None):
    """Página de gestión de usuario"""
    try:
        datos = session.execute(text("SELECT email, grado FROM usuarios WHERE id = :id"), 
                              {"id": usuario["user_id"]}).fetchone()
        if not datos:
            return RedirectResponse(url="/")
        
        return templates.TemplateResponse("usuario.html", {
            "request": request,
            "user_id": usuario["user_id"],
            "email": datos[0],
            "grado": datos[1]
        })
    except:
        return RedirectResponse(url="/")

@router.post("/editar-usuario")
async def editar(request: Request, new_email: str = Form(...),
                new_password: str = Form(None), new_grado: str = Form(...),
                usuario: dict = Depends(requerir_autenticacion),
                session: SessionDepends = None):
    """Editar datos del usuario"""
    try:
        user_id = usuario["user_id"]
        
        if new_password:
            # Si hay nueva contraseña, encriptarla
            password_encriptada = pwd_context.hash(new_password)
            session.execute(text("""
                UPDATE usuarios SET email = :email, password = :pass, grado = :grado 
                WHERE id = :id
            """), {"email": new_email, "pass": password_encriptada, "grado": new_grado, "id": user_id})
        else:
            session.execute(text("""
                UPDATE usuarios SET email = :email, grado = :grado WHERE id = :id
            """), {"email": new_email, "grado": new_grado, "id": user_id})
        
        session.commit()
        
        # Crear nuevo token con los datos actualizados
        nuevo_token = crear_token(
            data={"user_id": user_id, "grado": new_grado},
            expires_delta=timedelta(minutes=480)
        )
        
        response = RedirectResponse(url="/usuario", status_code=303)
        response.set_cookie(
            key="access_token",
            value=nuevo_token,
            httponly=True,
            max_age=480 * 60,
            samesite="lax"
        )
        
        return response
    except:
        session.rollback()
        return RedirectResponse(url="/usuario", status_code=303)

@router.post("/eliminar-usuario")
async def eliminar(request: Request, confirm_password: str = Form(...),
                  usuario: dict = Depends(requerir_autenticacion),
                  session: SessionDepends = None):
    """Eliminar cuenta de usuario"""
    try:
        user_id = usuario["user_id"]
        
        # Verificar contraseña antes de eliminar
        datos_usuario = session.execute(text("SELECT password FROM usuarios WHERE id = :id"), 
                                {"id": user_id}).fetchone()
        
        if not datos_usuario or not pwd_context.verify(confirm_password, datos_usuario[0]):
            return RedirectResponse(url="/usuario", status_code=303)
        
        # Eliminar estudiante y resultados
        estudiante = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                                    {"id": user_id}).fetchone()
        
        if estudiante:
            est_id = estudiante[0]
            session.execute(text("DELETE FROM resultados WHERE id_estudiantes = :id"), {"id": est_id})
            session.execute(text("DELETE FROM estudiantes WHERE id = :id"), {"id": est_id})
        
        # Eliminar usuario
        session.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": user_id})
        session.commit()
        
        # Cerrar sesión
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie("access_token")
        return response
        
    except:
        session.rollback()
        return RedirectResponse(url="/usuario", status_code=303)