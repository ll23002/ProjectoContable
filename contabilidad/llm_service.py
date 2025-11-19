import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from pgvector.django import L2Distance

from contabilidad.models import Cuenta

load_dotenv()

_embedding_model = None

def get_embedding_model():
    """
    Patrón Singleton para cargar el modelo solo cuando se necesita
    y evitar que la aplicación explote al arrancar.
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            print("⏳ Cargando modelo ligero (MiniLM-L12)...")
            # Modelo ligero de 384 dimensiones. Mucho más rápido y estable.
            _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ ¡Modelo cargado en memoria!")
        except Exception as e:
            print(f"❌ ERROR FATAL cargando el modelo: {e}")
            raise e
    return _embedding_model

def clasificar_transaccion(descripcion: str, precomputed_embedding=None):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY en el archivo .env")

        client = genai.Client(api_key=api_key)

        if precomputed_embedding is not None:
            transaccion_embedding = precomputed_embedding
        else:
            embedding_model = get_embedding_model()
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