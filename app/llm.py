import httpx
from app.config import settings

async def call_gemini_api(prompt: str) -> str:
    """Realiza una petición directa por HTTP a la API de Google Gemini (3.1 Flash Lite)."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "tu_gemini_api_key_aqui":
        return "Error: No se ha configurado la clave GEMINI_API_KEY en tu archivo .env. Por favor, edita tu archivo .env y agrega una clave válida."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,       # Temperatura baja para que sea factual y no alucine
            "maxOutputTokens": 1000   # Suficiente para respuestas explicativas detalladas
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                # Extraer la respuesta del formato de Gemini
                try:
                    text_response = data["candidates"][0]["content"]["parts"][0]["text"]
                    return text_response.strip()
                except (KeyError, IndexError):
                    return "Error al procesar la respuesta de Gemini. Estructura inesperada en el JSON devuelto."
            else:
                # Si hay error, intentar leer el detalle
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except Exception:
                    pass
                return f"Error en la API de Gemini (Código {response.status_code}): {error_detail}"
    except httpx.RequestError as exc:
        return f"Error de conexión con la API de Gemini: {exc}"

async def call_openai_api(prompt: str) -> str:
    """Realiza una petición directa por HTTP a la API de OpenAI (gpt-4o-mini)."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "tu_openai_api_key_aqui":
        return "Error: No se ha configurado la clave OPENAI_API_KEY en tu archivo .env. Por favor, edita tu archivo .env y agrega una clave válida."

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-4o-mini",       # Modelo rápido y económico
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                try:
                    text_response = data["choices"][0]["message"]["content"]
                    return text_response.strip()
                except (KeyError, IndexError):
                    return "Error al procesar la respuesta de OpenAI. Estructura inesperada en el JSON devuelto."
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("error", {}).get("message", error_detail)
                except Exception:
                    pass
                return f"Error en la API de OpenAI (Código {response.status_code}): {error_detail}"
    except httpx.RequestError as exc:
        return f"Error de conexión con la API de OpenAI: {exc}"

async def generate_llm_response(prompt: str) -> str:
    """Función de orquestación para llamar al proveedor de LLM configurado."""
    provider = settings.LLM_PROVIDER
    if provider == "gemini":
        return await call_gemini_api(prompt)
    elif provider == "openai":
        return await call_openai_api(prompt)
    else:
        return f"Error: Proveedor de LLM '{provider}' no soportado. Configura LLM_PROVIDER en 'gemini' o 'openai' en tu archivo .env."
