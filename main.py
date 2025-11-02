from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from rutas.autenticacion import router as router_autenticacion
from rutas.paginas import router as router_paginas
from rutas.usuario import router as router_usuario
from rutas.preguntas import router as router_preguntas

app = FastAPI(title="PREPARICFES")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Manejador de excepciones para redirección
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Maneja las excepciones HTTP, especialmente las de autenticación"""
    if exc.status_code == 303 and "Location" in exc.headers:
        # Es una redirección de autenticación
        return RedirectResponse(url=exc.headers["Location"], status_code=303)
    
    # Para otros errores HTTP, redirigir al inicio
    if exc.status_code in [401, 403]:
        return RedirectResponse(url="/", status_code=303)
    
    # Para otros casos, dejar que FastAPI lo maneje normalmente
    return RedirectResponse(url="/", status_code=303)

# Rutas
app.include_router(router_autenticacion, tags=["Autenticación"])
app.include_router(router_paginas, tags=["Páginas"])
app.include_router(router_usuario, tags=["Usuario"])
app.include_router(router_preguntas, tags=["Preguntas"])