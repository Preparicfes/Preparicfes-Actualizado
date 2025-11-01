from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from db import SessionDepends
from seguridad.autenticacion import requerir_autenticacion
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Configuración de materias
MATERIAS = {
    "matematicas": {"nombre": "Matemáticas", "color": "#FFA29E", "img": "sonrisaMate.png"},
    "ingles": {"nombre": "Inglés", "color": "#CCB5F8", "img": "sonrisa.png"},
    "sociales": {"nombre": "Sociales y Ciudadanas", "color": "#FFFAB9", "img": "sonrisasociales.png"},
    "lectura": {"nombre": "Lectura Crítica", "color": "#81CBF6", "img": "imagensonrisalectura.png"},
    "ciencias": {"nombre": "Ciencias Naturales", "color": "#C7F683", "img": "cienciasonriosa.png"}
}

MATERIAS_BD = {
    "matematicas": ["Matemáticas", "Matematicas", "MATEMÁTICAS"],
    "ingles": ["Inglés", "Ingles", "INGLÉS", "English"],
    "sociales": ["Ciencias Sociales", "Sociales y Ciudadanas", "Sociales"],
    "lectura": ["Lectura Crítica", "Lectura Critica"],
    "ciencias": ["Ciencias Naturales", "Ciencias"]
}

@router.get("/preguntas/{materia}", response_class=HTMLResponse)
async def preguntas(request: Request, materia: str, 
                   usuario: dict = Depends(requerir_autenticacion)):
    """Muestra las preguntas de una materia"""
    config = MATERIAS.get(materia)
    if not config:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    
    return templates.TemplateResponse("preguntas_dinamicas.html", {
        "request": request,
        "materia": materia,
        "nombre_materia": config["nombre"],
        "color_materia": config["color"],
        "imagen_materia": config["img"],
        "user_id": usuario["user_id"],
        "grado": usuario["grado"]
    })

@router.get("/api/preguntas/{materia}")
async def obtener_preguntas(materia: str, usuario: dict = Depends(requerir_autenticacion),
                           session: SessionDepends = None):
    """API para obtener las preguntas de una materia"""
    try:
        # Buscar el área
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
        
        # Convertir grado a número
        grados = {"9": 9, "10": 10, "11": 11}
        grado_num = grados.get(str(usuario["grado"]), int(usuario["grado"]))
        
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

@router.post("/api/guardar-respuestas")
async def guardar_respuestas(request: Request, usuario: dict = Depends(requerir_autenticacion),
                            session: SessionDepends = None):
    """Guarda las respuestas del estudiante"""
    try:
        data = await request.json()
        materia = data.get("materia")
        respuestas = data.get("respuestas", [])
        
        if not all([materia, respuestas]):
            raise HTTPException(status_code=400, detail="Datos incompletos")
        
        user_id = usuario["user_id"]
        
        # Calcular puntaje
        correctas = sum(1 for r in respuestas if r.get("correcta"))
        total = len(respuestas)
        puntaje = (correctas / total) * 100 if total > 0 else 0
        
        # Obtener o crear estudiante
        est = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                            {"id": user_id}).fetchone()
        
        if not est:
            grados = {"9": 9, "10": 10, "11": 11}
            grado_num = grados.get(str(usuario["grado"]), int(usuario["grado"]))
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
    
@router.get("/Resul", response_class=HTMLResponse, name="Resul")
async def resultados(request: Request, usuario: dict = Depends(requerir_autenticacion),
                    session: SessionDepends = None):
    """Muestra los resultados del estudiante"""
    try:
        # Buscar estudiante
        est = session.execute(text("SELECT id FROM estudiantes WHERE id_usuario = :id"), 
                            {"id": usuario["user_id"]}).fetchone()
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
            
            # Calcular desempeño
            for r in results:
                puntaje = r[1]
                if puntaje >= 90:
                    desempeno = "Superior"
                elif puntaje >= 70:
                    desempeno = "Alto"
                elif puntaje >= 50:
                    desempeno = "Medio"
                else:
                    desempeno = "Bajo"
                
                resultados.append({
                    "materia": r[0],
                    "puntaje": puntaje,
                    "desempeno": desempeno
                })
        
        # Calcular promedio
        promedio = sum(r["puntaje"] for r in resultados) / len(resultados) if resultados else 0
        
        return templates.TemplateResponse("Resul.html", {
            "request": request,
            "user_id": usuario["user_id"],
            "grado": usuario["grado"],
            "resultados": resultados,
            "promedio": round(promedio, 2)
        })
        
    except Exception as e:
        print(f"Error en resultados: {e}")
        return templates.TemplateResponse("Resul.html", {
            "request": request,
            "user_id": usuario["user_id"],
            "grado": usuario["grado"],
            "resultados": [],
            "promedio": 0
        })