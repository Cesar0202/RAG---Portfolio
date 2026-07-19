# AI RAG Engine (Bot de Telegram y Panel Web)

Este proyecto implementa un sistema de Generación Aumentada por Recuperación (RAG) local y ligero, desacoplado en una API de **FastAPI**, una base de datos vectorial **ChromaDB**, embeddings locales con **Sentence-Transformers** (`all-MiniLM-L6-v2`), generación con **Gemini/OpenAI** y dos interfaces de usuario: un **Bot de Telegram** y un **Panel Web interactivo (modo oscuro)**.

---

## Estructura del Proyecto

```text
bot RAG/
├── .env                  # Variables de entorno (Token de bot, claves de API)
├── requirements.txt      # Librerías de Python requeridas
├── run.py                # Ejecutable principal (inicia FastAPI y Telegram Bot en paralelo)
├── test_local_rag.py     # Script para pruebas de integración local
├── app/
│   ├── config.py         # Carga y validación de configuración (.env)
│   ├── embeddings.py     # Manejo del modelo de embeddings (Singleton)
│   ├── database.py       # Interfaz con ChromaDB (búsqueda y listado)
│   ├── ingest.py         # Extracción de texto y algoritmo de chunking
│   ├── llm.py            # Clientes HTTP asíncronos para Gemini/OpenAI
│   └── bot.py            # Cliente y comandos del Bot de Telegram
├── data/                 # Almacenamiento local persistente de Chroma
└── docs/                 # Carpeta para colocar PDFs y TXT a indexar
```

---

## Requisitos Previos

1. **Python 3.8 o superior** instalado.
2. **Tokens / Claves de API:**
   * **Telegram Bot Token:** Pídelo al bot oficial `@BotFather` en Telegram.
   * **Google Gemini API Key:** Solicítala de forma gratuita en [Google AI Studio].

---

## Configuración y Ejecución Local (Windows / Mac / Linux)

### 1. Configurar variables de entorno
Edita el archivo `.env` en la raíz del proyecto y completa los siguientes campos:
```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aqui
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
```

### 2. Crear entorno virtual e instalar dependencias
Abre tu terminal y ejecuta:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Probar el sistema de consulta (RAG Local)
Puedes correr el script de prueba para verificar que el chunking, la indexación y la búsqueda en Chroma funcionan perfectamente
```bash
python test_local_rag.py
```

### 4. Iniciar la aplicación completa
Para arrancar el panel web de FastAPI y el Bot de Telegram en paralelo corre
```bash
python run.py
```
* **Panel Web:** Accede a `http://localhost:8000` en tu navegador.
* **Bot de Telegram:** Abre chat con tu bot en Telegram y escribe `/start`.

---
