import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

class Settings:
    # Token de Telegram y Chat ID
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Proveedor de LLM (gemini o openai)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()

    # Claves de API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Base de datos y documentos
    CHROMA_DB_DIR: str = os.getenv("CHROMA_DB_DIR", "./data/chroma")
    DOCS_DIR: str = os.getenv("DOCS_DIR", "./docs")

    # Servidor FastAPI
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # Configuración de RAG
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"  # Ligero, eficiente, corre en CPU
    CHUNK_SIZE: int = 1200                          # Tamaño en caracteres (aprox 300 tokens)
    CHUNK_OVERLAP: int = 200                       # Solape en caracteres

    @property
    def is_gemini_enabled(self) -> bool:
        return self.LLM_PROVIDER == "gemini" and bool(self.GEMINI_API_KEY)

    @property
    def is_openai_enabled(self) -> bool:
        return self.LLM_PROVIDER == "openai" and bool(self.OPENAI_API_KEY)

settings = Settings()
