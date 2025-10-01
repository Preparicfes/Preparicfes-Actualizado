from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
 
app = FastAPI()
templates = Jinja2Templates (directory="templates")
app.mount("/static", StaticFiles (directory="static"), name="static")

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/registrate", response_class=HTMLResponse, name="registrate")
async def registrate(request: Request):
    return templates.TemplateResponse("registrate.html", {"request": request})

@app.get("/intro", response_class=HTMLResponse, name="intro")
async def intro(request: Request):
    return templates.TemplateResponse("intro.html", {"request": request})

@app.get("/criterio", response_class=HTMLResponse, name="criterio")
async def criterio(request: Request):
    return templates.TemplateResponse("criterio.html", {"request": request})

@app.get("/competencias", response_class=HTMLResponse, name="competencias")
async def competencias(request: Request):
    return templates.TemplateResponse("competencias.html", {"request": request})


@app.get("/pregun1mat", response_class=HTMLResponse, name="pregun1mat")
async def pregun1mat(request: Request):
    return templates.TemplateResponse("pregun1mat.html", {"request": request})


@app.get("/pregun2mat", response_class=HTMLResponse, name="pregun2mat")
async def pregun2mat(request: Request):
    return templates.TemplateResponse("pregun2mat.html", {"request": request})


@app.get("/pregun3mat", response_class=HTMLResponse, name="pregun3mat")
async def pregun3mat(request: Request):
    return templates.TemplateResponse("pregun3mat.html", {"request": request})


@app.get("/pregun1ing", response_class=HTMLResponse, name="pregun1ing")
async def pregun1ing(request: Request):
    return templates.TemplateResponse("pregun1ing.html", {"request": request})


@app.get("/pregun2ing", response_class=HTMLResponse, name="pregun2ing")
async def pregun2ing(request: Request):
    return templates.TemplateResponse("pregun2ing.html", {"request": request})


@app.get("/pregun3ing", response_class=HTMLResponse, name="pregun3ing")
async def pregun3ing(request: Request):
    return templates.TemplateResponse("pregun3ing.html", {"request": request})


@app.get("/pregunsoc1", response_class=HTMLResponse, name="pregunsoc1")
async def pregunsoc1(request: Request):
    return templates.TemplateResponse("pregunsoc1.html", {"request": request})


@app.get("/pregunsoc2", response_class=HTMLResponse, name="pregunsoc2")
async def pregunsoc2(request: Request):
    return templates.TemplateResponse("pregunsoc2.html", {"request": request})

@app.get("/pregunsoc3", response_class=HTMLResponse, name="pregunsoc3")
async def pregunsoc3(request: Request):
    return templates.TemplateResponse("pregunsoc3.html", {"request": request})


@app.get("/pregunlec1", response_class=HTMLResponse, name="pregunlec1")
async def pregunlec1(request: Request):
    return templates.TemplateResponse("pregunlec1.html", {"request": request})


@app.get("/pregunlec2", response_class=HTMLResponse, name="pregunlec2")
async def pregunlec2(request: Request):
    return templates.TemplateResponse("pregunlec2.html", {"request": request})


@app.get("/pregunlec3", response_class=HTMLResponse, name="pregunlec3")
async def pregunlec3(request: Request):
    return templates.TemplateResponse("pregunlec3.html", {"request": request})


@app.get("/preguncien1", response_class=HTMLResponse, name="preguncien1")
async def preguncien1(request: Request):
    return templates.TemplateResponse("preguncien1.html", {"request": request})


@app.get("/preguncien2", response_class=HTMLResponse, name="preguncien2")
async def preguncien2(request: Request):
    return templates.TemplateResponse("preguncien2.html", {"request": request})


@app.get("/preguncien3", response_class=HTMLResponse, name="preguncien3")
async def preguncien3(request: Request):
    return templates.TemplateResponse("preguncien3.html", {"request": request})


@app.get("/Resul", response_class=HTMLResponse, name="Resul")
async def Resul(request: Request):
    return templates.TemplateResponse("Resul.html", {"request": request})


