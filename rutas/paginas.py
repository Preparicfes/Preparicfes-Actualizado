from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from seguridad.autenticacion import requerir_autenticacion

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/intro", response_class=HTMLResponse, name="intro")
async def intro(request: Request, usuario: dict = Depends(requerir_autenticacion)):
    """Página de introducción - requiere estar autenticado"""
    return templates.TemplateResponse("intro.html", {
        "request": request,
        "user_id": usuario["user_id"],
        "grado": usuario["grado"]
    })

@router.get("/criterio", response_class=HTMLResponse, name="criterio")
async def criterio(request: Request, usuario: dict = Depends(requerir_autenticacion)):
    """Página de criterios - requiere estar autenticado"""
    return templates.TemplateResponse("criterio.html", {
        "request": request,
        "user_id": usuario["user_id"],
        "grado": usuario["grado"]
    })

@router.get("/competencias", response_class=HTMLResponse, name="competencias")
async def competencias(request: Request, usuario: dict = Depends(requerir_autenticacion)):
    """Página de competencias - requiere estar autenticado"""
    return templates.TemplateResponse("competencias.html", {
        "request": request,
        "user_id": usuario["user_id"],
        "grado": usuario["grado"]
    })