import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from app.config import settings

# Configurar logs básicos
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL base para comunicarse con la API local de FastAPI
BACKEND_URL = f"http://localhost:{settings.PORT}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manda mensaje de bienvenida y comandos disponibles."""
    welcome_text = (
        "🤖 **¡Hola! Soy tu Asistente Bot RAG**\n\n"
        "Estoy conectado a una base de datos de conocimiento. "
        "Pregúntame cualquier cosa sobre los manuales y documentos cargados y te responderé con la información exacta.\n\n"
        "📌 **Comandos Disponibles:**\n"
        "🔹 `/ingest` - Escanear la carpeta de documentos e indexarlos.\n"
        "🔹 `/files` - Mostrar los archivos indexados actualmente.\n"
        "🔹 `/clear` - Vaciar toda la base de datos de conocimiento.\n\n"
        "✍️ Simplemente **escríbeme tu pregunta** y buscaré la respuesta."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def ingest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invoca el endpoint de ingesta de FastAPI."""
    await update.message.reply_text("🔄 Indexando documentos de la carpeta 'docs/', por favor espera...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{BACKEND_URL}/ingest")
            if response.status_code == 200:
                data = response.json()
                status_msg = (
                    f"✅ **¡Ingesta completada!**\n\n"
                    f"📁 Archivos procesados: `{data.get('processed_files_count', 0)}` de {len(data.get('files', []))}\n"
                    f"🧩 Fragmentos creados: `{data.get('total_chunks', 0)}`"
                )
                await update.message.reply_text(status_msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Error al procesar los documentos en el backend.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error al conectar con el backend de FastAPI: {e}")

async def files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista los archivos indexados."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/files")
            if response.status_code == 200:
                files = response.json().get("files", [])
                if not files:
                    await update.message.reply_text("📭 No hay documentos indexados todavía en la base de datos. Coloca archivos en la carpeta `docs/` y corre `/ingest`.")
                else:
                    files_str = "\n".join([f"📄 `{f}`" for f in files])
                    await update.message.reply_text(f"📚 **Documentos Indexados:**\n\n{files_str}", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Error al obtener los archivos del backend.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error de conexión: {e}")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Limpia la base de datos vectorial."""
    await update.message.reply_text("⚠️ Borrando base de datos...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{BACKEND_URL}/clear")
            if response.status_code == 200:
                await update.message.reply_text("🗑️ **¡Base de datos vaciada con éxito!** Todo el conocimiento anterior ha sido eliminado.", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Error al vaciar la base de datos.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error de conexión: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la pregunta del usuario, la envía al backend y devuelve la respuesta + fuentes."""
    user_query = update.message.text
    # Enviar un estado de "escribiendo" en Telegram para mejor UX
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/query",
                json={"question": user_query, "n_results": 4}
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "")
                sources = data.get("sources", [])
                
                # Dar formato a las fuentes
                if sources:
                    sources_list = []
                    for s in sources:
                        # Para TXTs, no mostramos página 1 redundante
                        if s.get("page") == 1 and s.get("file", "").endswith(".txt"):
                            sources_list.append(f"📄 `{s.get('file')}`")
                        else:
                            sources_list.append(f"📄 `{s.get('file')}` (Pág. {s.get('page')})")
                    
                    sources_str = "\n\n📖 **Fuentes Citadas:**\n" + "\n".join(sources_list)
                else:
                    sources_str = ""
                
                # Responder al usuario
                await update.message.reply_text(f"{answer}{sources_str}", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ El backend devolvió un error al procesar tu pregunta.")
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        await update.message.reply_text(f"❌ Error de conexión con el backend de RAG: {e}")

def get_bot_app():
    """Construye y configura la aplicación del Bot de Telegram."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or token == "tu_telegram_bot_token_aqui":
        logger.warning("TELEGRAM_BOT_TOKEN no configurado o tiene valor por defecto. El Bot de Telegram estará desactivado.")
        return None
        
    application = ApplicationBuilder().token(token).build()
    
    # Agregar manejadores de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ingest", ingest_command))
    application.add_handler(CommandHandler("files", files_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Manejar mensajes de texto normales (preguntas)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application
