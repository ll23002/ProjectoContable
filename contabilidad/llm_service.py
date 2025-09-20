import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from pgvector.django import L2Distance

from contabilidad.models import Cuenta

load_dotenv()

# Se carga el modelo 'jina-embeddings-v4' de SentenceTransformer.
# Convierte la descripción de la transacción en un
# vector numérico (embedding) que capture su significado semántico.
try:
    print("Cargando el modelo de SentenceTransformer (puede tardar)...")
    embedding_model = SentenceTransformer('jinaai/jina-embeddings-v4', trust_remote_code=True)
    print("¡Modelo de SentenceTransformer cargado!")
except Exception as e:
    embedding_model = None
    print(f"ERROR: No se pudo cargar el modelo de SentenceTransformer: {e}")


def clasificar_transaccion(descripcion: str, precomputed_embedding=None):
    """
    Implementa un patrón de RAG (Retrieval-Augmented Generation)
    para maximizar la precisión y relevancia de la clasificación:

    1.  **Fase de Recuperación (Retrieval):** La descripción de la transacción
        es codificada en un embedding por el modelo SentenceTransformer. Este
        embedding se usa para ejecutar una búsqueda de similitud semántica (L2Distance)
        contra los vectores de las cuentas en la base de datos, recuperando
        las 5 candidatas más probables.

    2.  **Fase de Generación Aumentada (Augmented Generation):** Un prompt
        detallado, que incluye la descripción original y las 5 cuentas recuperadas,
        es enviado al modelo Gemini. Esto obliga al modelo a basar su razonamiento
        en un conjunto de datos relevante y controlado, quien finalmente genera
        la clasificación y justificación en un formato JSON estructurado.

    Args:
        descripcion (str): Descripción de la transacción a clasificar.

    Returns:
        str: Un string con formato JSON que contiene la clasificación, incluyendo
             tipo de transacción, categoría, cuenta sugerida, nivel de
             confianza y una justificación textual.

    Raises:
        Exception: Si el modelo de embeddings no está disponible.
        ValueError: Si no se encuentra la clave API en el archivo .env.
    """
    if not embedding_model:
        raise Exception("El modelo de embeddings no está disponible.")

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY en el archivo .env")

        client = genai.Client(api_key=api_key)

        if precomputed_embedding is not None:
            transaccion_embedding = precomputed_embedding
        else:
            transaccion_embedding = embedding_model.encode(descripcion, task ="retrieval")


        cuentas_similares = Cuenta.objects.order_by(
            L2Distance('embedding', transaccion_embedding)
        )[:5]

        texto_cuentas_candidatas = "\\n".join([
            f"- Código: {c.codigo_cuenta}, Nombre: {c.nombre_cuenta}"
            for c in cuentas_similares
        ])

        prompt = f"""
        Analiza la siguiente transacción contable: "{descripcion}"

        He realizado una búsqueda y he encontrado las 5 cuentas contables más relevantes de nuestro catálogo:
        {texto_cuentas_candidatas}

        Por favor, elige el **código de cuenta** más apropiado de la lista anterior para esta transacción.

        Devuelve únicamente un objeto JSON válido con la siguiente estructura exacta:
        {{
          "tipo_transaccion": "INGRESO" o "EGRESO",
          "categoria": "el nombre de la categoría contable más apropiada",
          "cuenta_sugerida": "el código de la cuenta que elegiste de la lista de 5 opciones",
          "confianza": un número decimal entre 0.0 y 1.0,
          "justificacion": "una explicación breve de por qué elegiste esa cuenta de la lista"
        }}
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return response.text

    except Exception as e:
        print(f"Error durante la clasificación: {e}")
        return None