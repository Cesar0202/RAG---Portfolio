import threading
import uvicorn
import time
import sys
from app.main import app
from app.config import settings
from app.bot import get_bot_app

def run_fastapi():
    """Ejecuta el servidor FastAPI con Uvicorn."""
    try:
        uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")
    except Exception as e:
        print(f"Error crítico en el servidor FastAPI: {e}", file=sys.stderr)

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    print("=" * 60)
    print("           AI RAG ENGINE - INICIANDO SISTEMA")
    print("=" * 60)

    # 1. Iniciar FastAPI en un hilo secundario (background)
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    
    # Esperar a que el servidor FastAPI levante e imprima sus logs
    time.sleep(2.0)
    
    # 2. Inicializar y correr el Bot de Telegram
    bot_app = get_bot_app()
    if bot_app:
        print("\n[Bot] Iniciando Bot de Telegram en modo Polling...")
        print("Presiona Ctrl+C para detener el sistema completo.")
        try:
            # run_polling() es bloqueante, captura señales del sistema (como Ctrl+C)
            # y apaga el bot y el hilo de FastAPI limpiamente.
            bot_app.run_polling()
        except KeyboardInterrupt:
            print("\nDeteniendo bot de Telegram...")
    else:
        print("\n[Aviso] Bot de Telegram DESACTIVADO (TOKEN no configurado o inválido en .env)")
        print(f"[Web] Puedes interactuar usando el Panel Web en: http://localhost:{settings.PORT}")
        print("Presiona Ctrl+C para detener el sistema.")
        try:
            # Si el bot no está activo, mantenemos el hilo principal corriendo
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    print("\n[+] Sistema detenido con éxito.")
