import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from db import SessionDepends
from datetime import datetime
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# === PÁGINAS ===

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/registrate", response_class=HTMLResponse, name="registrate")
async def registrate(request: Request):
    return templates.TemplateResponse("registrate.html", {"request": request})

# === AUTENTICACIÓN ===

@app.post("/registrar")
async def registrar(request: Request, email: str = Form(...), password: str = Form(...), 
                   grado: str = Form(...), session: SessionDepends = None):
    try:
        # Verificar si existe
        existe = session.execute(text("SELECT id FROM usuarios WHERE email = :email"), 
                                {"email": email}).fetchone()
        if existe:
            return templates.TemplateResponse("registrate.html", 
                {"request": request, "error": "Este correo ya está registrado"})
        
        # Crear usuario
        session.execute(text("""
            INSERT INTO usuarios (email, password, grado, fecha_registro)
            VALUES (:email, :password, :grado, :fecha)
        """), {"email": email, "password": password, "grado": grado, "fecha": datetime.now()})
        session.commit()
        
        return RedirectResponse(url="/?registro=exitoso", status_code=303)
        
    except Exception as e:
        session.rollback()
        return templates.TemplateResponse("registrate.html", 
            {"request": request, "error": f"Error: {str(e)}"})

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), 
               session: SessionDepends = None):
    try:
        usuario = session.execute(text("""
            SELECT id, password, grado FROM usuarios WHERE email = :email
        """), {"email": email}).fetchone()
        
        if not usuario or password != usuario[1]:
            return templates.TemplateResponse("index.html", 
                {"request": request, "error": "Correo o contraseña incorrectos"})
        
        return RedirectResponse(url=f"/intro?user_id={usuario[0]}&grado={usuario[2]}", 
                              status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse("index.html", 
            {"request": request, "error": "Error al iniciar sesión"})

# === NAVEGACIÓN ===

@app.get("/intro", response_class=HTMLResponse, name="intro")
async def intro(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("intro.html", 
        {"request": request, "user_id": user_id, "grado": grado})

@app.get("/criterio", response_class=HTMLResponse, name="criterio")
async def criterio(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("criterio.html", 
        {"request": request, "user_id": user_id, "grado": grado})

@app.get("/competencias", response_class=HTMLResponse, name="competencias")
async def competencias(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("competencias.html", 
        {"request": request, "user_id": user_id, "grado": grado})

# === USUARIO ===

@app.get("/usuario", response_class=HTMLResponse, name="usuario")
async def usuario(request: Request, user_id: Optional[int] = None, 
                 grado: Optional[str] = None, session: SessionDepends = None):
    if not user_id:
        return RedirectResponse(url="/")
    
    try:
        datos = session.execute(text("SELECT email, grado FROM usuarios WHERE id = :id"), 
                              {"id": user_id}).fetchone()
        if not datos:
            return RedirectResponse(url="/")
        
        return templates.TemplateResponse("usuario.html", 
            {"request": request, "user_id": user_id, "email": datos[0], "grado": datos[1]})
    except:
        return RedirectResponse(url="/")

@app.post("/editar-usuario")
async def editar(request: Request, user_id: int = Form(...), new_email: str = Form(...),
                new_password: Optional[str] = Form(None), new_grado: str = Form(...), 
                session: SessionDepends = None):
    try:
        if new_password:
            session.execute(text("""
                UPDATE usuarios SET email = :email, password = :pass, grado = :grado 
                WHERE id = :id
            """), {"email": new_email, "pass": new_password, "grado": new_grado, "id": user_id})
        else:
            session.execute(text("""
                UPDATE usuarios SET email = :email, grado = :grado WHERE id = :id
            """), {"email": new_email, "grado": new_grado, "id": user_id})
        session.commit()
        return RedirectResponse(url=f"/usuario?user_id={user_id}&grado={new_grado}", status_code=303)
    except:
        session.rollback()
        return RedirectResponse(url=f"/usuario?user_id={user_id}&grado={new_grado}", status_code=303)

@app.post("/eliminar-usuario")
async def eliminar(request: Request, user_id: int = Form(...), 
                  confirm_password: str = Form(...), session: SessionDepends = None):
    try:
        # Verificar contraseña
        usuario = session.execute(text("SELECT password FROM usuarios WHERE id = :id"), 
                                {"id": user_id}).fetchone()
        if not usuario or usuario[0] != confirm_password:
            return RedirectResponse(url=f"/usuario?user_id={user_id}", status_code=303)
        
        # Obtener estudiante
        estudiante = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                                    {"id": user_id}).fetchone()
        
        if estudiante:
            est_id = estudiante[0]
            session.execute(text("DELETE FROM resultados WHERE id_estudiantes = :id"), {"id": est_id})
            session.execute(text("DELETE FROM estudiantes WHERE id = :id"), {"id": est_id})
        
        session.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": user_id})
        session.commit()
        return RedirectResponse(url="/", status_code=303)
        
    except:
        session.rollback()
        return RedirectResponse(url=f"/usuario?user_id={user_id}", status_code=303)

# === PREGUNTAS ===

# Configuración de materias
MATERIAS = {
    "matematicas": {"nombre": "Matemáticas", "color": "#FFA29E", "img": "sonrisaMate.png"},
    "ingles": {"nombre": "Inglés", "color": "#CCB5F8", "img": "sonrisa.png"},
    "sociales": {"nombre": "Sociales y Ciudadanas", "color": "#FFFAB9", "img": "sonrisasociales.png"},
    "lectura": {"nombre": "Lectura Crítica", "color": "#81CBF6", "img": "imagensonrisalectura.png"},
    "ciencias": {"nombre": "Ciencias Naturales", "color": "#C7F683", "img": "cienciasonriosa.png"}
}

# Mapeo de nombres de materias en BD
MATERIAS_BD = {
    "matematicas": ["Matemáticas", "Matematicas", "MATEMÁTICAS"],
    "ingles": ["Inglés", "Ingles", "INGLÉS", "English"],
    "sociales": ["Ciencias Sociales", "Sociales y Ciudadanas", "Sociales"],
    "lectura": ["Lectura Crítica", "Lectura Critica"],
    "ciencias": ["Ciencias Naturales", "Ciencias"]
}

@app.get("/preguntas/{materia}", response_class=HTMLResponse)
async def preguntas(request: Request, materia: str, user_id: Optional[int] = None, 
                   grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    
    config = MATERIAS.get(materia)
    if not config:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    
    return templates.TemplateResponse("preguntas_dinamicas.html", {
        "request": request, "materia": materia, "nombre_materia": config["nombre"],
        "color_materia": config["color"], "imagen_materia": config["img"],
        "user_id": user_id, "grado": grado
    })

@app.get("/api/preguntas/{materia}")
async def get_preguntas(materia: str, grado: str, session: SessionDepends = None):
    try:
        # Buscar área
        nombres = MATERIAS_BD.get(materia)
        if not nombres:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        area_id = None
        for nombre in nombres:
            result = session.execute(text("SELECT id FROM areas WHERE nombre_materia = :n"), 
                                   {"n": nombre}).fetchone()
            if result:
                area_id = result[0]
                break
        
        if not area_id:
            raise HTTPException(status_code=404, detail="Área no encontrada")
        
        # Convertir grado
        grados = {"6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11}
        grado_num = grados.get(str(grado), int(grado))
        
        # Obtener ID del grado
        grado_id = session.execute(text("SELECT id FROM grado WHERE numero_grado = :n"), 
                                  {"n": grado_num}).scalar()
        if not grado_id:
            raise HTTPException(status_code=404, detail="Grado no encontrado")
        
        # Obtener 6 preguntas aleatorias
        preguntas = session.execute(text("""
            SELECT id, enunciado, opcion_a, opcion_b, opcion_c, opcion_d, 
                   imagen, respuesta_correcta
            FROM preguntas WHERE id_areas = :area AND id_grado = :grado
            ORDER BY RANDOM() LIMIT 6
        """), {"area": area_id, "grado": grado_id}).fetchall()
        
        return {
            "preguntas": [{
                "id": p[0], "numero": i+1, "enunciado": p[1],
                "opcion_a": p[2], "opcion_b": p[3], "opcion_c": p[4], "opcion_d": p[5],
                "imagen": p[6], "respuesta_correcta": p[7]
            } for i, p in enumerate(preguntas)],
            "total": len(preguntas)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/guardar-respuestas")
async def guardar(request: Request, session: SessionDepends = None):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        materia = data.get("materia")
        respuestas = data.get("respuestas", [])
        
        if not all([user_id, materia, respuestas]):
            raise HTTPException(status_code=400, detail="Datos incompletos")
        
        # Calcular puntaje
        correctas = sum(1 for r in respuestas if r.get("correcta"))
        total = len(respuestas)
        puntaje = (correctas / total) * 100 if total > 0 else 0
        
        # Obtener o crear estudiante
        est = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                            {"id": user_id}).fetchone()
        
        if not est:
            # Crear estudiante
            grado_usuario = session.execute(text("SELECT grado FROM usuarios WHERE id = :id"), 
                                          {"id": user_id}).scalar()
            grados = {"6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11}
            grado_num = grados.get(str(grado_usuario), int(grado_usuario))
            grado_id = session.execute(text("SELECT id FROM grado WHERE numero_grado = :n"), 
                                     {"n": grado_num}).scalar()
            
            est_id = session.execute(text("""
                INSERT INTO estudiantes (id_usuario, id_grado) VALUES (:u, :g) RETURNING id
            """), {"u": user_id, "g": grado_id}).scalar()
        else:
            est_id = est[0]
        
        # Obtener ID del área
        nombres = MATERIAS_BD.get(materia, [])
        area_id = None
        for nombre in nombres:
            result = session.execute(text("SELECT id FROM areas WHERE nombre_materia = :n"), 
                                   {"n": nombre}).fetchone()
            if result:
                area_id = result[0]
                break
        
        # Guardar resultado
        session.execute(text("""
            INSERT INTO resultados (id_estudiantes, id_areas, fecha, puntaje_final)
            VALUES (:est, :area, :fecha, :puntaje)
        """), {"est": est_id, "area": area_id, "fecha": datetime.now(), "puntaje": int(puntaje)})
        session.commit()
        
        return {"success": True, "correctas": correctas, "total": total, "puntaje": round(puntaje, 2)}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# === RESULTADOS ===

@app.get("/Resul", response_class=HTMLResponse, name="Resul")
async def resultados(request: Request, user_id: Optional[int] = None, 
                    grado: Optional[str] = None, session: SessionDepends = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    
    try:
        est = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                            {"id": user_id}).fetchone()
        resultados = []
        
        if est:
            est_id = est[0]
            # Obtener solo el resultado más reciente por materia
            results = session.execute(text("""
                WITH UltimosResultados AS (
                    SELECT 
                        id_areas,
                        puntaje_final,
                        ROW_NUMBER() OVER (PARTITION BY id_areas ORDER BY fecha DESC) as rn
                    FROM resultados
                    WHERE id_estudiantes = :id
                )
                SELECT a.nombre_materia, ur.puntaje_final
                FROM UltimosResultados ur
                JOIN areas a ON ur.id_areas = a.id
                WHERE ur.rn = 1
                ORDER BY a.nombre_materia
            """), {"id": est_id}).fetchall()
            
            for r in results:
                puntaje = r[1]
                desempeno = "Superior" if puntaje >= 90 else "Alto" if puntaje >= 70 else "Medio" if puntaje >= 50 else "Bajo"
                resultados.append({"materia": r[0], "puntaje": puntaje, "desempeno": desempeno})
        
        promedio = sum(r["puntaje"] for r in resultados) / len(resultados) if resultados else 0
        
        return templates.TemplateResponse("Resul.html", {
            "request": request, "user_id": user_id, "grado": grado,
            "resultados": resultados, "promedio": round(promedio, 2)
        })
        
    except Exception as e:
        print(f"Error en resultados: {e}")
        return templates.TemplateResponse("Resul.html", {
            "request": request, "user_id": user_id, "grado": grado,
            "resultados": [], "promedio": 0
        })