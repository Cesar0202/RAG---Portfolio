import os
import pypdf
from app.config import settings
from app.database import db_manager

def split_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    """Divide un texto largo en fragmentos respetando límites de palabras e implementando solape."""
    chunks = []
    text = text.strip()
    text_len = len(text)
    
    if text_len <= chunk_size:
        return [text]
    
    start = 0
    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Intentar no cortar palabras buscando el último espacio en blanco
        if end < text_len:
            last_space = text.rfind(' ', start, end)
            # Solo cortamos si encontramos un espacio razonablemente alejado del inicio del chunk
            if last_space != -1 and last_space > start + (chunk_size // 2):
                end = last_space + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        start = end - overlap
        
        # Si el inicio del siguiente es mayor al texto o ya procesamos hasta el final, salimos
        if start >= text_len or end == text_len:
            break
            
    return chunks

def extract_text_from_pdf(filepath: str) -> list[dict]:
    """Extrae el texto de un PDF página por página para conservar los metadatos de las fuentes."""
    pages_data = []
    try:
        reader = pypdf.PdfReader(filepath)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_data.append({
                    "page": i + 1,
                    "text": text
                })
    except Exception as e:
        print(f"Error leyendo el PDF {filepath}: {e}")
    return pages_data

def extract_text_from_txt(filepath: str) -> str:
    """Extrae el texto de un archivo TXT plano."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error leyendo el TXT {filepath}: {e}")
        return ""

def ingest_all_documents() -> dict:
    """Escanea la carpeta de documentos, procesa los archivos nuevos o actualizados y los guarda en Chroma."""
    docs_dir = settings.DOCS_DIR
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        return {"processed": 0, "status": "Carpeta 'docs/' creada. Coloca archivos en ella."}

    files = [f for f in os.listdir(docs_dir) if f.endswith(('.pdf', '.txt'))]
    if not files:
        return {"processed": 0, "status": "No se encontraron archivos PDF o TXT en la carpeta 'docs/'."}

    collection = db_manager.get_collection()
    processed_count = 0
    total_chunks_added = 0
    
    for filename in files:
        filepath = os.path.join(docs_dir, filename)
        
        # 1. Limpieza preventiva: eliminamos los chunks previos de este archivo para evitar duplicados
        # si se actualiza el contenido.
        try:
            collection.delete(where={"source": filename})
        except Exception as e:
            print(f"No había registros previos para {filename}: {e}")

        chunks_to_add = []
        metadatas_to_add = []
        ids_to_add = []

        # 2. Extracción y fragmentación
        if filename.endswith('.pdf'):
            pages = extract_text_from_pdf(filepath)
            for page_info in pages:
                page_num = page_info["page"]
                page_text = page_info["text"]
                
                # Dividir el texto de la página
                page_chunks = split_text(page_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
                
                for idx, chunk in enumerate(page_chunks):
                    chunks_to_add.append(chunk)
                    metadatas_to_add.append({"source": filename, "page": page_num})
                    ids_to_add.append(f"{filename}_p{page_num}_c{idx}")
        
        elif filename.endswith('.txt'):
            full_text = extract_text_from_txt(filepath)
            if full_text:
                txt_chunks = split_text(full_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
                for idx, chunk in enumerate(txt_chunks):
                    chunks_to_add.append(chunk)
                    metadatas_to_add.append({"source": filename, "page": 1})
                    ids_to_add.append(f"{filename}_c{idx}")
        
        # 3. Guardar en ChromaDB
        if chunks_to_add:
            db_manager.add_chunks(
                chunks=chunks_to_add,
                ids=ids_to_add,
                metadatas=metadatas_to_add
            )
            processed_count += 1
            total_chunks_added += len(chunks_to_add)
            print(f"Indexado: '{filename}' en {len(chunks_to_add)} fragmentos.")

    return {
        "processed_files_count": processed_count,
        "total_chunks": total_chunks_added,
        "files": files,
        "status": f"Se procesaron {processed_count} archivos y se generaron {total_chunks_added} fragmentos."
    }
