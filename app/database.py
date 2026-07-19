import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from app.config import settings
from app.embeddings import embeddings_manager

class ChromaEmbeddingFunction(EmbeddingFunction):
    """Enlace personalizado para usar nuestro EmbeddingModelManager dentro de ChromaDB."""
    def __call__(self, input: Documents) -> Embeddings:
        return embeddings_manager.get_embeddings(input)

class VectorDatabaseManager:
    def __init__(self):
        self.db_dir = settings.CHROMA_DB_DIR
        self._client = None
        self.embedding_function = ChromaEmbeddingFunction()

    @property
    def client(self):
        if self._client is None:
            # Crea un cliente de Chroma persistente en el directorio configurado
            self._client = chromadb.PersistentClient(path=self.db_dir)
        return self._client

    def get_collection(self, name: str = "rag_documents"):
        """Obtiene o crea una colección de Chroma DB usando nuestro modelo de embeddings."""
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}  # Usar similitud de coseno para búsqueda semántica
        )

    def add_chunks(self, chunks: list[str], ids: list[str], metadatas: list[dict], collection_name: str = "rag_documents"):
        """Inserta fragmentos de texto en la base de datos vectorial."""
        if not chunks:
            return
        collection = self.get_collection(collection_name)
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

    def query(self, query_text: str, n_results: int = 4, collection_name: str = "rag_documents") -> list[dict]:
        """Busca los fragmentos más similares a la consulta del usuario."""
        collection = self.get_collection(collection_name)
        
        # Realiza la búsqueda vectorial
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Reformatear la salida para que sea fácil de consumir en el RAG
        formatted_results = []
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
            ids = results["ids"][0]
            
            for doc, meta, dist, chunk_id in zip(documents, metadatas, distances, ids):
                formatted_results.append({
                    "id": chunk_id,
                    "content": doc,
                    "metadata": meta,
                    "score": 1.0 - dist  # Convertir distancia a score de similitud (aproximado)
                })
        
        return formatted_results

    def list_indexed_files(self, collection_name: str = "rag_documents") -> list[str]:
        """Lista los nombres únicos de archivos que han sido indexados en la colección."""
        collection = self.get_collection(collection_name)
        data = collection.get(include=["metadatas"])
        
        if not data or not data["metadatas"]:
            return []
        
        # Extraer el nombre de archivo único de los metadatas de los chunks
        files = set()
        for meta in data["metadatas"]:
            if meta and "source" in meta:
                files.add(meta["source"])
        
        return sorted(list(files))

    def clear_database(self, collection_name: str = "rag_documents"):
        """Elimina la colección completa para reiniciar la base de datos."""
        try:
            self.client.delete_collection(name=collection_name)
            print(f"Colección '{collection_name}' eliminada correctamente.")
        except Exception as e:
            print(f"No se pudo eliminar la colección (puede que no exista): {e}")

# Instancia singleton para interactuar con Chroma DB
db_manager = VectorDatabaseManager()
