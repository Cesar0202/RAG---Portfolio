import os
import shutil
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.config import settings
from app.database import db_manager
from app.ingest import ingest_all_documents
from app.llm import generate_llm_response

app = FastAPI(
    title="RAG Engine Backend",
    description="API para búsqueda semántica e ingesta de documentos",
    version="1.0.0"
)

# Configurar políticas CORS para permitir peticiones desde cualquier origen (útil para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Cargar el modelo de embeddings de forma ansiosa para evitar demoras en la primera consulta
    from app.embeddings import embeddings_manager
    from app.database import db_manager
    print("Pre-cargando modelo de embeddings...")
    _ = embeddings_manager.model
    print("Pre-cargando conexión a ChromaDB...")
    _ = db_manager.get_collection()
    print("¡Pre-carga completada!")


# Modelos de datos para las peticiones
class QueryRequest(BaseModel):
    question: str
    n_results: int = 15
    history: list[dict] = []

class QueryResponse(BaseModel):
    response: str
    sources: list[dict]

def update_metrics(duration: float):
    try:
        import json
        import datetime
        metrics_file = os.path.join("data", "metrics.json")
        os.makedirs("data", exist_ok=True)
        
        data = {
            "total_queries": 0,
            "average_response_time": 0.0,
            "total_tokens_estimated": 0,
            "queries_by_day": {
                "Lun": 0, "Mar": 0, "Mié": 0, "Jue": 0, "Vie": 0, "Sáb": 0, "Dom": 0
            }
        }
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
                
        prev_total = data.get("total_queries", 0)
        new_total = prev_total + 1
        data["total_queries"] = new_total
        
        prev_avg = data.get("average_response_time", 0.0)
        new_avg = (prev_avg * prev_total + duration) / new_total
        data["average_response_time"] = round(new_avg, 2)
        
        data["total_tokens_estimated"] = data.get("total_tokens_estimated", 0) + 250
        
        days_map = {
            "Mon": "Lun", "Tue": "Mar", "Wed": "Mié", "Thu": "Jue", "Fri": "Vie", "Sat": "Sáb", "Sun": "Dom"
        }
        day_en = datetime.datetime.now().strftime("%a")
        day_es = days_map.get(day_en, "Lun")
        
        queries_by_day = data.get("queries_by_day", {})
        queries_by_day[day_es] = queries_by_day.get(day_es, 0) + 1
        data["queries_by_day"] = queries_by_day
        
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error al actualizar métricas: {e}")

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Realiza la búsqueda semántica en ChromaDB y genera la respuesta con el LLM."""
    try:
        import time
        start_time = time.time()
        
        # 1. Obtener fragmentos relevantes
        results = db_manager.query(request.question, n_results=request.n_results)
        
        if not results:
            return QueryResponse(
                response="La base de datos de conocimiento está vacía o no se encontraron fragmentos relevantes. Por favor, coloca archivos PDF o TXT en la carpeta 'docs/' y ejecute la ingesta (/ingest).",
                sources=[]
            )
            
        # 2. Construir el prompt estructurado para el RAG
        context_str = ""
        unique_sources = []
        seen_sources = set()
        
        for idx, res in enumerate(results):
            source = res["metadata"].get("source", "Desconocido")
            page = res["metadata"].get("page", 1)
            content = res["content"]
            
            # Formatear el contexto para el prompt
            context_str += f"\n--- FRAGMENTO {idx+1} (Fuente: {source}, Pág. {page}) ---\n{content}\n"
            
            # Registrar fuentes únicas para el frontend
            source_key = f"{source}_p{page}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                unique_sources.append({
                    "file": source,
                    "page": page
                })
                
        # Añadir historial reciente si existe
        history_str = ""
        if request.history:
            history_str = "\nHistorial reciente de la conversación:\n"
            for msg in request.history[-6:]:  # Últimos 6 mensajes
                role_name = "Usuario" if msg.get("role") == "user" else "Tú (César)"
                history_str += f"{role_name}: {msg.get('content')}\n"
            history_str += "\n--- Fin del historial ---\n"

        # Inyectar proyectos dinámicamente en el contexto
        try:
            import json
            with open("data/projects.json", "r", encoding="utf-8") as f:
                projects_data = json.load(f)
            if projects_data:
                context_str += "\n--- MIS PROYECTOS DE PORTAFOLIO ---\n"
                for p in projects_data:
                    context_str += f"- Proyecto: {p.get('title', '')}\n  Descripción: {p.get('description', '')}\n  Tecnologías: {p.get('technologies', '')}\n"
        except Exception:
            pass

        prompt = f"""Tú eres César Huamán Uriarte. Debes responder siempre en primera persona (yo, mi, me, mis, etc.), hablando directamente como César.
Usa la información de los siguientes fragmentos del contexto para responder la pregunta del usuario. NO inventes información que no esté en el contexto.
IMPORTANTE: Cuando te pregunten sobre tu experiencia laboral, dale prioridad a tus logros y rol en "IPTV PERU", extrayendo detalles precisos del contexto. Menciona a "Agroindustrial BETA" de pasada.
IMPORTANTE: Cuando te pregunten "sobre ti" o "cuéntame de ti", incluye tanto tus capacidades profesionales como tu lado PERSONAL (tus gustos, pasatiempos o historia de vida que estén en el contexto).
IMPORTANTE: Si te preguntan por herramientas, habilidades o proyectos, busca exhaustivamente en el contexto y lístalas SIEMPRE usando viñetas (bullet points) para que la lectura sea estructurada y no un bloque de texto amontonado.
IMPORTANTE: Debes ser EXTREMADAMENTE CONCISO y DIRECTO. Resume la información al máximo, idealmente en un solo párrafo corto o un par de líneas. NO des respuestas largas ni detalladas innecesariamente.
Si la información en el contexto no es suficiente para responder la pregunta, di exactamente: "No encontré suficiente información en los documentos cargados para responder a esa pregunta."
No utilices tus conocimientos externos para complementar información que no esté directamente sustentada en el contexto.
IMPORTANTE: NUNCA menciones los nombres de los archivos o documentos (por ejemplo .txt, .pdf) de los que obtienes la información, ni reveles al usuario una lista de los documentos que tienes cargados.
Si el usuario pregunta específicamente qué documentos tienes, cómo fuiste entrenado, o pide detalles sobre tus archivos fuente, responde exactamente: "Esa información es confidencial y no puedo suministrártela."
{history_str}
Contexto:
{context_str}

Pregunta del Usuario: {request.question}

Respuesta del Asistente (en primera persona como César):"""

        # 3. Consultar el LLM
        llm_response = await generate_llm_response(prompt)
        
        # 4. Registrar métricas reales
        duration = time.time() - start_time
        update_metrics(duration)
        
        return QueryResponse(
            response=llm_response,
            sources=unique_sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en el motor RAG: {e}")

@app.post("/ingest")
async def trigger_ingest():
    """Llama a la ingesta de documentos para procesar los PDFs y TXTs de la carpeta docs/."""
    try:
        result = ingest_all_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la ingesta: {e}")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Sube un archivo PDF o TXT al servidor y lo guarda en la carpeta docs/."""
    try:
        filename = file.filename
        if not filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF o TXT.")
            
        docs_dir = settings.DOCS_DIR
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
            
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"filename": filename, "status": "Archivo subido con éxito."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el archivo: {e}")

@app.get("/files")
async def list_files():
    """Lista los archivos que han sido indexados en la base de datos."""
    try:
        files = db_manager.list_indexed_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener archivos indexados: {e}")

@app.post("/clear")
async def clear_db():
    """Limpia todos los documentos indexados de la base de datos vectorial."""
    try:
        db_manager.clear_database()
        return {"status": "Base de datos vaciada con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al vaciar la base de datos: {e}")

class FeedbackRequest(BaseModel):
    name: str
    email: str
    message: str

class AuthRequest(BaseModel):
    password: str

@app.post("/feedback")
async def receive_feedback(request: FeedbackRequest):
    """Guarda comentarios de contacto en un archivo local data/feedback.json y envía alerta a Telegram."""
    try:
        import json
        feedback_file = os.path.join("data", "feedback.json")
        os.makedirs("data", exist_ok=True)
        
        comments = []
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    comments = json.load(f)
            except Exception:
                pass
                
        import datetime
        comments.append({
            "name": request.name,
            "email": request.email,
            "message": request.message,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
            
        # Enviar notificación a Telegram si está configurado
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID and settings.TELEGRAM_CHAT_ID != "tu_chat_id_aqui":
            try:
                import httpx
                telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                text = (
                    f"📩 *Nuevo Comentario en Portafolio*\n\n"
                    f"👤 *Nombre:* {request.name}\n"
                    f"✉️ *Correo:* {request.email}\n\n"
                    f"💬 *Mensaje:*\n{request.message}"
                )
                async with httpx.AsyncClient() as client:
                    await client.post(telegram_url, json={
                        "chat_id": int(settings.TELEGRAM_CHAT_ID),
                        "text": text,
                        "parse_mode": "Markdown"
                    })
            except Exception as telegram_err:
                print(f"Error al enviar notificación a Telegram: {telegram_err}")
                
        return {"status": "Comentario guardado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar comentario: {e}")

@app.post("/admin/auth")
async def admin_auth(request: AuthRequest):
    """Verifica si la contraseña coincide con ADMIN_PASSWORD."""
    if request.password == settings.ADMIN_PASSWORD:
        return {"auth": True, "message": "Autenticación exitosa."}
    else:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

class ProjectRequest(BaseModel):
    title: str
    description: str
    technologies: str
    github: str = ""
    demo: str = ""
    image: str = ""

@app.get("/metrics")
async def get_metrics():
    """Retorna las métricas reales del sistema."""
    try:
        import json
        metrics_file = os.path.join("data", "metrics.json")
        if not os.path.exists(metrics_file):
            default_metrics = {
                "total_queries": 0,
                "average_response_time": 0.0,
                "total_tokens_estimated": 0,
                "queries_by_day": {
                    "Lun": 0, "Mar": 0, "Mié": 0, "Jue": 0, "Vie": 0, "Sáb": 0, "Dom": 0
                }
            }
            return default_metrics
        with open(metrics_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {e}")

@app.get("/projects")
async def get_projects():
    """Retorna la lista de proyectos para mostrar en el portafolio."""
    try:
        import json
        projects_file = os.path.join("data", "projects.json")
        if not os.path.exists(projects_file):
            os.makedirs("data", exist_ok=True)
            default_projects = [
                {
                    "title": "Sistema Multiplataforma de Aprendizaje Adaptativo",
                    "description": "Plataforma educativa inteligente (Tesis) desarrollada para UNMSM que utiliza Machine Learning para predecir necesidades de aprendizaje y adaptar el contenido en tiempo real.",
                    "technologies": "Flutter, FastAPI, scikit-learn, XGBoost, Python",
                    "github": "https://github.com/Cesar0202",
                    "demo": "",
                    "image": ""
                },
                {
                    "title": "Asistente RAG Local Inteligente",
                    "description": "El motor de RAG local actual en el que te encuentras chateando. Indexa documentos de forma vectorial en ChromaDB y responde usando Gemini 3.1.",
                    "technologies": "FastAPI, ChromaDB, Gemini 3.1 Flash Lite, HTML/CSS/JS",
                    "github": "https://github.com/Cesar0202",
                    "demo": "",
                    "image": ""
                }
            ]
            with open(projects_file, "w", encoding="utf-8") as f:
                json.dump(default_projects, f, ensure_ascii=False, indent=2)
            return default_projects
        with open(projects_file, "r", encoding="utf-8") as f:
            raw_projects = json.load(f)
        
        # Mapeo robusto por si existen proyectos antiguos en projects.json
        projects = []
        for p in raw_projects:
            projects.append({
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "technologies": p.get("technologies", ""),
                "github": p.get("github", p.get("link", "")),
                "demo": p.get("demo", ""),
                "image": p.get("image", "")
            })
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {e}")

@app.post("/projects")
async def add_project(project: ProjectRequest):
    """Guarda un nuevo proyecto en el archivo projects.json."""
    try:
        import json
        projects_file = os.path.join("data", "projects.json")
        os.makedirs("data", exist_ok=True)
        
        projects = []
        if os.path.exists(projects_file):
            try:
                with open(projects_file, "r", encoding="utf-8") as f:
                    projects = json.load(f)
            except Exception:
                pass
                
        projects.append({
            "title": project.title,
            "description": project.description,
            "technologies": project.technologies,
            "github": project.github,
            "demo": project.demo,
            "image": project.image
        })
        
        with open(projects_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
            
        return {"status": "Proyecto agregado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar proyecto: {e}")

@app.put("/projects/{index}")
async def update_project(index: int, project: ProjectRequest):
    """Actualiza un proyecto existente por su índice."""
    try:
        import json
        projects_file = os.path.join("data", "projects.json")
        if not os.path.exists(projects_file):
            raise HTTPException(status_code=404, detail="No hay proyectos registrados.")
            
        with open(projects_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
            
        if index < 0 or index >= len(projects):
            raise HTTPException(status_code=404, detail="Índice de proyecto fuera de rango.")
            
        # Actualizar campos, preservando la imagen si no se envía una nueva
        projects[index] = {
            "title": project.title,
            "description": project.description,
            "technologies": project.technologies,
            "github": project.github,
            "demo": project.demo,
            "image": project.image if project.image else projects[index].get("image", "")
        }
        
        with open(projects_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
            
        return {"status": "Proyecto actualizado con éxito."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {e}")

@app.delete("/projects/{index}")
async def delete_project(index: int):
    """Elimina un proyecto por su índice en la lista."""
    try:
        import json
        projects_file = os.path.join("data", "projects.json")
        if not os.path.exists(projects_file):
            raise HTTPException(status_code=404, detail="No hay proyectos registrados.")
            
        with open(projects_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
            
        if index < 0 or index >= len(projects):
            raise HTTPException(status_code=400, detail="Índice de proyecto fuera de rango.")
            
        projects.pop(index)
        
        with open(projects_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
            
        return {"status": "Proyecto eliminado con éxito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar proyecto: {e}")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Sirve la interfaz web de usuario premium con diseño en modo oscuro y responsivo."""
    # Intentar leer desde static/index.html, si no existe devolvemos un HTML básico
    static_file_path = os.path.join("static", "index.html")
    if os.path.exists(static_file_path):
        with open(static_file_path, "r", encoding="utf-8") as f:
            return f.read()
            
    # Fallback HTML en caso de que no se encuentre el archivo
    return """
    <html>
        <head><title>RAG Bot Dashboard</title></head>
        <body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding-top: 100px;">
            <h1>RAG Engine Backend</h1>
            <p>El backend está en línea. La interfaz de usuario premium no se ha encontrado en <code>static/index.html</code>.</p>
        </body>
    </html>
    """

# Servir archivos estáticos (para las imágenes de las habilidades y descargas de CV)
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
