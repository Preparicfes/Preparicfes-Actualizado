from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rutas.autenticacion import router as router_autenticacion
from rutas.paginas import router as router_paginas
from rutas.usuario import router as router_usuario
from rutas.preguntas import router as router_preguntas

app = FastAPI(title="PREPARICFES")

app.mount("/static", StaticFiles(directory="static"), name="static")

#rutas
app.include_router(router_autenticacion, tags=["Autenticación"])
app.include_router(router_paginas, tags=["Páginas"])
app.include_router(router_usuario, tags=["Usuario"])
app.include_router(router_preguntas, tags=["Preguntas"])