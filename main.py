import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from db import SessionDepends
from datetime import datetime
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- RUTAS DE PÁGINAS ---

@app.get("/", response_class=HTMLResponse, name="index")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/registrate", response_class=HTMLResponse, name="registrate")
async def registrate(request: Request):
    return templates.TemplateResponse("registrate.html", {"request": request})


# --- RUTAS DE AUTENTICACIÓN ---

@app.post("/registrar")
async def registrar_usuario(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    grado: str = Form(...),
    session: SessionDepends = None
):
    """
    Registra un nuevo usuario en la base de datos
    """
    try:
        print(f"📧 Intentando registrar: {email}, grado: {grado}")
        
        # Verificar si el usuario ya existe
        query_check = text("SELECT id FROM usuarios WHERE email = :email")
        result = session.execute(query_check, {"email": email}).fetchone()
        
        if result:
            print(f"⚠️ El usuario {email} ya existe")
            return templates.TemplateResponse(
                "registrate.html",
                {
                    "request": request,
                    "error": "Este correo ya está registrado"
                }
            )
        
        # Insertar nuevo usuario (sin cifrar contraseña)
        print("💾 Insertando usuario en la base de datos...")
        query_insert = text("""
            INSERT INTO usuarios (email, password, grado, fecha_registro)
            VALUES (:email, :password, :grado, :fecha_registro)
        """)
        
        session.execute(query_insert, {
            "email": email,
            "password": password,
            "grado": grado,
            "fecha_registro": datetime.now()
        })
        session.commit()
        
        print(f"✅ Usuario {email} registrado exitosamente")
        
        # Redirigir al index con mensaje de éxito
        return RedirectResponse(
            url="/?registro=exitoso",
            status_code=303
        )
        
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR COMPLETO: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "registrate.html",
            {
                "request": request,
                "error": f"Error al registrar usuario: {str(e)}"
            }
        )


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: SessionDepends = None
):
    """
    Valida las credenciales del usuario
    """
    try:
        print(f"🔐 Intentando login: {email}")
        
        # Buscar usuario por email
        query = text("""
            SELECT id, email, password, grado 
            FROM usuarios 
            WHERE email = :email
        """)
        
        result = session.execute(query, {"email": email}).fetchone()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if not result or password != result[2]:
            print(f"❌ Login fallido para: {email}")
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": "Correo o contraseña incorrectos"
                }
            )
        
        user_id = result[0]
        grado = result[3]
        
        print(f"✅ Login exitoso: user_id={user_id}, grado={grado}")
        
        # Login exitoso - redirigir a la página de introducción
        return RedirectResponse(
            url=f"/intro?user_id={user_id}&grado={grado}",
            status_code=303
        )
        
    except Exception as e:
        print(f"❌ Error en login: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Error al iniciar sesión. Intenta de nuevo."
            }
        )


# --- RUTAS DE NAVEGACIÓN ---

@app.get("/intro", response_class=HTMLResponse, name="intro")
async def intro(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("intro.html", {
        "request": request,
        "user_id": user_id,
        "grado": grado
    })

@app.get("/criterio", response_class=HTMLResponse, name="criterio")
async def criterio(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("criterio.html", {
        "request": request,
        "user_id": user_id,
        "grado": grado
    })

@app.get("/competencias", response_class=HTMLResponse, name="competencias")
async def competencias(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    return templates.TemplateResponse("competencias.html", {
        "request": request,
        "user_id": user_id,
        "grado": grado
    })


# --- RUTAS DINÁMICAS PARA PREGUNTAS ---

@app.get("/preguntas/{materia}", response_class=HTMLResponse)
async def preguntas_materia(
    request: Request,
    materia: str,
    user_id: Optional[int] = None,
    grado: Optional[str] = None
):
    """
    Muestra las preguntas de una materia específica
    """
    # Validar que user_id y grado estén presentes
    if not user_id or not grado:
        return RedirectResponse(url="/")
    
    # Mapeo de nombres de materia y colores
    materias_config = {
        "matematicas": {
            "nombre": "Matemáticas",
            "color": "#FFA29E",
            "imagen": "sonrisaMate.png"
        },
        "ingles": {
            "nombre": "Inglés",
            "color": "#CCB5F8",
            "imagen": "sonrisa.png"
        },
        "sociales": {
            "nombre": "Sociales y Ciudadanas",
            "color": "#FFFAB9",
            "imagen": "sonrisasociales.png"
        },
        "lectura": {
            "nombre": "Lectura Crítica",
            "color": "#81CBF6",
            "imagen": "imagensonrisalectura.png"
        },
        "ciencias": {
            "nombre": "Ciencias Naturales",
            "color": "#C7F683",
            "imagen": "cienciasonriosa.png"
        }
    }
    
    config = materias_config.get(materia)
    
    if not config:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    
    return templates.TemplateResponse("preguntas_dinamicas.html", {
        "request": request,
        "materia": materia,
        "nombre_materia": config["nombre"],
        "color_materia": config["color"],
        "imagen_materia": config["imagen"],
        "user_id": user_id,
        "grado": grado
    })


@app.get("/api/preguntas/{materia}")
async def get_preguntas(
    materia: str,
    grado: str,
    offset: int = 0,
    limit: int = 2,
    session: SessionDepends = None
):
    """
    API para obtener preguntas de una materia y grado específicos
    """
    try:
        # Mapeo de nombres de materia
        materias_map = {
            "matematicas": ["Matemáticas", "Matematicas", "MATEMÁTICAS", "MATEMATICAS"],
            "ingles": ["Inglés", "Ingles", "INGLÉS", "INGLES", "English"],
            "sociales": ["Ciencias Sociales", "Sociales y Ciudadanas", "Sociales", "CIENCIAS SOCIALES", "SOCIALES"],
            "lectura": ["Lectura Crítica", "Lectura Critica", "LECTURA CRÍTICA", "LECTURA CRITICA"],
            "ciencias": ["Ciencias Naturales", "Ciencias", "CIENCIAS NATURALES", "CIENCIAS"]
        }
        
        posibles_nombres = materias_map.get(materia)
        
        if not posibles_nombres:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        print(f"🔍 Buscando área: {materia}")
        
        # Buscar el área
        area_id = None
        for nombre in posibles_nombres:
            query_area = text("SELECT id FROM areas WHERE nombre_materia = :nombre")
            area_result = session.execute(query_area, {"nombre": nombre}).fetchone()
            
            if area_result:
                area_id = area_result[0]
                print(f"✅ Área encontrada - ID: {area_id}")
                break
        
        if not area_id:
            raise HTTPException(status_code=404, detail=f"Área no encontrada para '{materia}'")
        
        # Convertir grado a número si viene como texto
        grado_numeros = {
            "sexto": 6, "6": 6,
            "séptimo": 7, "septimo": 7, "7": 7,
            "octavo": 8, "8": 8,
            "noveno": 9, "9": 9,
            "décimo": 10, "decimo": 10, "10": 10,
            "once": 11, "11": 11
        }
        
        grado_numero = grado_numeros.get(str(grado).lower(), None)
        
        if not grado_numero:
            try:
                grado_numero = int(grado)
            except:
                raise HTTPException(status_code=400, detail=f"Grado inválido: {grado}")
        
        # Obtener ID del grado
        query_grado = text("SELECT id FROM grado WHERE numero_grado = :numero")
        grado_result = session.execute(query_grado, {"numero": grado_numero}).fetchone()
        
        if not grado_result:
            raise HTTPException(status_code=404, detail=f"Grado {grado} no encontrado")
        
        grado_id = grado_result[0]
        
        # Obtener 6 preguntas aleatorias
        query_preguntas = text("""
            SELECT id, enunciado, opcion_a, opcion_b, opcion_c, opcion_d, 
                   imagen, respuesta_correcta
            FROM preguntas
            WHERE id_areas = :area_id AND id_grado = :grado_id
            ORDER BY RANDOM()
            LIMIT 6
        """)
        
        todas_preguntas = session.execute(query_preguntas, {
            "area_id": area_id,
            "grado_id": grado_id
        }).fetchall()
        
        # Aplicar paginación
        inicio = offset
        fin = offset + limit
        preguntas_pagina = todas_preguntas[inicio:fin]
        
        total_preguntas = len(todas_preguntas)
        
        # Formatear respuesta
        preguntas_list = []
        for i, p in enumerate(preguntas_pagina):
            preguntas_list.append({
                "id": p[0],
                "numero": inicio + i + 1,
                "enunciado": p[1],
                "opcion_a": p[2],
                "opcion_b": p[3],
                "opcion_c": p[4],
                "opcion_d": p[5],
                "imagen": p[6],
                "respuesta_correcta": p[7]
            })
        
        return {
            "preguntas": preguntas_list,
            "total": total_preguntas,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_preguntas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo preguntas: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/guardar-respuestas")
async def guardar_respuestas(
    request: Request,
    session: SessionDepends = None
):
    """
    Guarda las respuestas del estudiante y calcula el puntaje
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        materia = data.get("materia")
        respuestas = data.get("respuestas", [])
        
        if not user_id or not materia or not respuestas:
            raise HTTPException(status_code=400, detail="Datos incompletos")
        
        # Calcular puntaje
        correctas = sum(1 for r in respuestas if r.get("correcta"))
        total = len(respuestas)
        puntaje_final = (correctas / total) * 100 if total > 0 else 0
        
        # Obtener o crear estudiante
        query_estudiante = text("SELECT id FROM estudiantes WHERE id_usuario = :user_id")
        estudiante = session.execute(query_estudiante, {"user_id": user_id}).fetchone()
        
        if not estudiante:
            # Obtener el grado del usuario
            query_grado_usuario = text("SELECT grado FROM usuarios WHERE id = :user_id")
            grado_usuario = session.execute(query_grado_usuario, {"user_id": user_id}).scalar()
            
            # Obtener el ID del grado
            query_grado_id = text("SELECT id FROM grado WHERE numero_grado = :numero")
            grado_id = session.execute(query_grado_id, {"numero": int(grado_usuario)}).scalar()
            
            # Crear estudiante
            query_insert_est = text("""
                INSERT INTO estudiantes (id_usuario, id_grado)
                VALUES (:user_id, :grado_id)
                RETURNING id
            """)
            estudiante_id = session.execute(query_insert_est, {
                "user_id": user_id,
                "grado_id": grado_id
            }).scalar()
        else:
            estudiante_id = estudiante[0]
        
        # Obtener ID del área
        materias_map = {
            "matematicas": ["Matemáticas", "Matematicas"],
            "ingles": ["Inglés", "Ingles"],
            "sociales": ["Ciencias Sociales", "Sociales y Ciudadanas", "Sociales"],
            "lectura": ["Lectura Crítica", "Lectura Critica"],
            "ciencias": ["Ciencias Naturales", "Ciencias"]
        }
        
        posibles_nombres = materias_map.get(materia, [])
        area_id = None
        
        for nombre in posibles_nombres:
            query_area = text("SELECT id FROM areas WHERE nombre_materia = :nombre")
            area_result = session.execute(query_area, {"nombre": nombre}).fetchone()
            if area_result:
                area_id = area_result[0]
                break
        
        # Guardar resultado
        query_resultado = text("""
            INSERT INTO resultados (id_estudiantes, id_areas, fecha, puntaje_final)
            VALUES (:estudiante_id, :area_id, :fecha, :puntaje)
        """)
        
        session.execute(query_resultado, {
            "estudiante_id": estudiante_id,
            "area_id": area_id,
            "fecha": datetime.now(),
            "puntaje": int(puntaje_final)
        })
        
        session.commit()
        
        return {
            "success": True,
            "correctas": correctas,
            "total": total,
            "puntaje": round(puntaje_final, 2)
        }
        
    except Exception as e:
        session.rollback()
        print(f"Error guardando respuestas: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/Resul", response_class=HTMLResponse, name="Resul")
async def Resul(
    request: Request,
    user_id: Optional[int] = None,
    grado: Optional[str] = None,
    session: SessionDepends = None
):
    """
    Muestra los resultados de todas las materias del estudiante
    """
    if not user_id or not grado:
        return RedirectResponse(url="/")
    
    try:
        # Obtener el estudiante
        query_estudiante = text("SELECT id FROM estudiantes WHERE id_usuario = :user_id")
        estudiante = session.execute(query_estudiante, {"user_id": user_id}).fetchone()
        
        resultados = []
        
        if estudiante:
            estudiante_id = estudiante[0]
            
            # Obtener resultados de todas las áreas
            query_resultados = text("""
                SELECT a.nombre_materia, r.puntaje_final, r.fecha
                FROM resultados r
                JOIN areas a ON r.id_areas = a.id
                WHERE r.id_estudiantes = :estudiante_id
                ORDER BY r.fecha DESC
            """)
            
            resultados_raw = session.execute(query_resultados, {
                "estudiante_id": estudiante_id
            }).fetchall()
            
            # Organizar resultados por materia (solo el más reciente)
            materias_vistas = set()
            for r in resultados_raw:
                materia = r[0]
                if materia not in materias_vistas:
                    materias_vistas.add(materia)
                    puntaje = r[1]
                    
                    # Determinar desempeño
                    if puntaje >= 90:
                        desempeno = "Superior"
                    elif puntaje >= 70:
                        desempeno = "Alto"
                    elif puntaje >= 50:
                        desempeno = "Medio"
                    else:
                        desempeno = "Bajo"
                    
                    resultados.append({
                        "materia": materia,
                        "puntaje": puntaje,
                        "desempeno": desempeno
                    })
        
        # Calcular promedio
        promedio = sum(r["puntaje"] for r in resultados) / len(resultados) if resultados else 0
        
        return templates.TemplateResponse("Resul.html", {
            "request": request,
            "user_id": user_id,
            "grado": grado,
            "resultados": resultados,
            "promedio": round(promedio, 2)
        })
        
    except Exception as e:
        print(f"Error obteniendo resultados: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("Resul.html", {
            "request": request,
            "user_id": user_id,
            "grado": grado,
            "resultados": [],
            "promedio": 0,
            "error": "Error al cargar resultados"
        })


# --- RUTAS ANTIGUAS PARA COMPATIBILIDAD ---

@app.get("/pregun1mat", response_class=HTMLResponse)
async def pregun1mat(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    return RedirectResponse(url=f"/preguntas/matematicas?user_id={user_id}&grado={grado}")

@app.get("/pregun1ing", response_class=HTMLResponse)
async def pregun1ing(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    return RedirectResponse(url=f"/preguntas/ingles?user_id={user_id}&grado={grado}")

@app.get("/pregunsoc1", response_class=HTMLResponse)
async def pregunsoc1(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    return RedirectResponse(url=f"/preguntas/sociales?user_id={user_id}&grado={grado}")

@app.get("/pregunlec1", response_class=HTMLResponse)
async def pregunlec1(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    return RedirectResponse(url=f"/preguntas/lectura?user_id={user_id}&grado={grado}")

@app.get("/preguncien1", response_class=HTMLResponse)
async def preguncien1(request: Request, user_id: Optional[int] = None, grado: Optional[str] = None):
    if not user_id or not grado:
        return RedirectResponse(url="/")
    return RedirectResponse(url=f"/preguntas/ciencias?user_id={user_id}&grado={grado}")