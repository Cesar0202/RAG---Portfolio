from sentence_transformers import SentenceTransformer
from app.config import settings

class EmbeddingModelManager:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModelManager, cls).__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            print(f"Cargando modelo de embeddings: {settings.EMBEDDING_MODEL_NAME}...")
            # Carga el modelo en CPU por defecto para ahorrar memoria y recursos
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")
            print("¡Modelo de embeddings cargado correctamente!")
        return self._model

    def get_embedding(self, text: str) -> list[float]:
        """Genera el embedding para una sola cadena de texto."""
        # Convierte el vector de numpy a una lista de floats nativa de Python
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Genera embeddings para una lista de textos de manera eficiente (batch)."""
        if not texts:
            return []
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

# Instancia singleton para ser importada en el proyecto
embeddings_manager = EmbeddingModelManager()
