import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy import text
from db import SessionDepends
from datetime import datetime
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Encripta una contraseña"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    return pwd_context.verify(plain_password, hashed_password)


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
        
        # Encriptar la contraseña
        print("🔒 Encriptando contraseña...")
        hashed_password = hash_password(password)
        
        # Insertar nuevo usuario
        print("💾 Insertando usuario en la base de datos...")
        query_insert = text("""
            INSERT INTO usuarios (email, password, grado, fecha_registro)
            VALUES (:email, :password, :grado, :fecha_registro)
        """)
        
        session.execute(query_insert, {
            "email": email,
            "password": hashed_password,
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
    Valida las credenciales del usuario y guarda info en sesión
    """
    try:
        # Buscar usuario por email
        query = text("""
            SELECT id, email, password, grado 
            FROM usuarios 
            WHERE email = :email
        """)
        
        result = session.execute(query, {"email": email}).fetchone()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if not result or not verify_password(password, result[2]):
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "error": "Correo o contraseña incorrectos"
                }
            )
        
        user_id = result[0]
        grado = result[3]
        
        # 🔍 DEBUG - Verificar valores
        print(f"✅ Login exitoso:")
        print(f"   - user_id: {user_id} (tipo: {type(user_id)})")
        print(f"   - grado: {grado} (tipo: {type(grado)})")
        print(f"   - URL de redirección: /intro?user_id={user_id}&grado={grado}")
        
        # Login exitoso - redirigir con parámetros de usuario
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
    
    # Mapeo de nombres de materia y colores (usando los mismos de comp.css)
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
    Retorna 2 preguntas por página de un total de 6 aleatorias
    """
    try:
        # Mapeo de nombres de materia - MÚLTIPLES VARIANTES PARA COMPATIBILIDAD
        materias_map = {
            "matematicas": [
                "Matemáticas",
                "Matematicas", 
                "MATEMÁTICAS",
                "MATEMATICAS"
            ],
            "ingles": [
                "Inglés",
                "Ingles",
                "INGLÉS",
                "INGLES",
                "English"
            ],
            "sociales": [
                "Ciencias Sociales",
                "Sociales y Ciudadanas",
                "Sociales",
                "CIENCIAS SOCIALES",
                "SOCIALES"
            ],
            "lectura": [
                "Lectura Crítica",
                "Lectura Critica",
                "LECTURA CRÍTICA",
                "LECTURA CRITICA",
                "Lectura crítica"
            ],
            "ciencias": [
                "Ciencias Naturales",
                "Ciencias",
                "CIENCIAS NATURALES",
                "CIENCIAS"
            ]
        }
        
        posibles_nombres = materias_map.get(materia)
        
        if not posibles_nombres:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        print(f"🔍 Buscando área: {materia}")
        print(f"   Probando nombres: {posibles_nombres}")
        
        # Intentar encontrar el área con cualquiera de los nombres posibles
        area_id = None
        nombre_encontrado = None
        
        for nombre in posibles_nombres:
            query_area = text("SELECT id, nombre_materia FROM areas WHERE nombre_materia = :nombre")
            area_result = session.execute(query_area, {"nombre": nombre}).fetchone()
            
            if area_result:
                area_id = area_result[0]
                nombre_encontrado = area_result[1]
                print(f"✅ Área encontrada - ID: {area_id}, Nombre: '{nombre_encontrado}'")
                break
        
        # Si no se encontró, intentar búsqueda case-insensitive y con LIKE
        if not area_id:
            print("⚠️ No encontrado con nombres exactos, intentando búsqueda flexible...")
            query_area_flexible = text("""
                SELECT id, nombre_materia 
                FROM areas 
                WHERE LOWER(nombre_materia) LIKE LOWER(:patron)
                LIMIT 1
            """)
            
            for nombre in posibles_nombres:
                patron = f"%{nombre.split()[0]}%"  # Usar primera palabra
                area_result = session.execute(query_area_flexible, {"patron": patron}).fetchone()
                
                if area_result:
                    area_id = area_result[0]
                    nombre_encontrado = area_result[1]
                    print(f"✅ Área encontrada (flexible) - ID: {area_id}, Nombre: '{nombre_encontrado}'")
                    break
        
        if not area_id:
            # Mostrar todas las áreas disponibles para debugging
            todas_areas = session.execute(text("SELECT id, nombre_materia FROM areas")).fetchall()
            print("❌ Área no encontrada. Áreas disponibles en la BD:")
            for a in todas_areas:
                print(f"   - ID {a[0]}: '{a[1]}'")
            raise HTTPException(
                status_code=404, 
                detail=f"Área no encontrada para '{materia}'. Revisa los nombres en la tabla 'areas'"
            )
        
        # Obtener ID del grado
        query_grado = text("SELECT id FROM grado WHERE numero_grado = :numero")
        grado_result = session.execute(query_grado, {"numero": int(grado)}).fetchone()
        
        if not grado_result:
            print(f"❌ Grado no encontrado: {grado}")
            raise HTTPException(status_code=404, detail=f"Grado {grado} no encontrado")
        
        grado_id = grado_result[0]
        print(f"✅ Grado encontrado - ID: {grado_id}")
        
        # Contar total de preguntas disponibles
        query_count = text("""
            SELECT COUNT(*) 
            FROM preguntas 
            WHERE id_areas = :area_id AND id_grado = :grado_id
        """)
        total_disponibles = session.execute(query_count, {
            "area_id": area_id,
            "grado_id": grado_id
        }).scalar()
        
        print(f"📊 Total de preguntas disponibles: {total_disponibles}")
        
        if total_disponibles == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No hay preguntas para {nombre_encontrado} grado {grado}"
            )
        
        # Obtener máximo 6 preguntas aleatorias (las guardamos para paginación)
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
        
        # Aplicar paginación sobre las 6 preguntas
        inicio = offset
        fin = offset + limit
        preguntas_pagina = todas_preguntas[inicio:fin]
        
        total_preguntas = min(len(todas_preguntas), 6)
        
        print(f"📄 Página actual: preguntas {inicio+1}-{min(fin, total_preguntas)} de {total_preguntas}")
        
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
        query_estudiante = text("""
            SELECT id FROM estudiantes WHERE id_usuario = :user_id
        """)
        estudiante = session.execute(query_estudiante, {"user_id": user_id}).fetchone()
        
        if not estudiante:
            # Obtener el grado del usuario
            query_grado_usuario = text("""
                SELECT grado FROM usuarios WHERE id = :user_id
            """)
            grado_usuario = session.execute(query_grado_usuario, {"user_id": user_id}).scalar()
            
            # Obtener el ID del grado
            query_grado_id = text("""
                SELECT id FROM grado WHERE numero_grado = :numero
            """)
            grado_id = session.execute(query_grado_id, {"numero": int(grado_usuario)}).scalar()
            
            # Crear estudiante si no existe
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
        
        # Obtener ID del área (usando la misma lógica flexible)
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
        query_estudiante = text("""
            SELECT id FROM estudiantes WHERE id_usuario = :user_id
        """)
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


# --- MANTENER RUTAS ANTIGUAS PARA COMPATIBILIDAD (redirigir a dinámicas) ---

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