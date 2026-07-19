import os
from app.ingest import ingest_all_documents
from app.database import db_manager
from app.config import settings

def run_integration_test():
    print("=" * 60)
    print("          INICIANDO PRUEBA DE INTEGRACIÓN RAG LOCAL")
    print("=" * 60)

    # 1. Crear un documento de prueba en la carpeta docs/
    docs_dir = settings.DOCS_DIR
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        
    test_file_path = os.path.join(docs_dir, "informacion_confidencial.txt")
    print(f"1. Creando archivo de prueba en: {test_file_path}")
    
    contenido_prueba = (
        "El protocolo de seguridad Omega-45 establece que el código de acceso súper secreto "
        "para el servidor de desarrollo en la nube es '9982-BLUE-ALPHA'.\n"
        "Este código cambia mensualmente y solo debe ser compartido con personal de nivel 3.\n"
        "El responsable directo de la infraestructura es el ingeniero Juan Pérez."
    )
    
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(contenido_prueba)

    # 2. Ejecutar la ingesta
    print("\n2. Ejecutando la ingesta de documentos...")
    ingest_result = ingest_all_documents()
    print("Resultado de la ingesta:", ingest_result)

    # 3. Consultar la base de datos vectorial
    pregunta = "¿Cuál es el código de acceso secreto para el servidor de desarrollo?"
    print(f"\n3. Consultando la base de datos semántica para: '{pregunta}'")
    
    resultados = db_manager.query(pregunta, n_results=1)
    
    print("\n" + "="*40)
    if resultados:
        doc = resultados[0]
        print("[OK] EXITO! Se encontro un fragmento relevante:")
        print(f"Archivo origen: {doc['metadata']['source']}")
        print(f"Puntuacion de similitud: {doc['score']:.4f}")
        print(f"Contenido extraido:\n{doc['content']}")
    else:
        print("[ERROR] No se recuperaron fragmentos de la base de datos.")
    print("="*40)

    print("\n4. Prueba completada con éxito.")

if __name__ == "__main__":
    run_integration_test()
