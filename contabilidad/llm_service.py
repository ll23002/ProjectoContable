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
    global _embedding_model
    if _embedding_model is None:
        try:
            print("⏳ Cargando modelo ligero (MiniLM-L12)...")
            _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ ¡Modelo cargado en memoria!")
        except Exception as e:
            print(f"❌ ERROR FATAL cargando el modelo: {e}")
            raise e
    return _embedding_model


def clasificar_transaccion(descripcion: str, monto: float, precomputed_embedding=None):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Falta la API KEY")

        client = genai.Client(api_key=api_key)

        if precomputed_embedding is not None:
            transaccion_embedding = precomputed_embedding
        else:
            embedding_model = get_embedding_model()
            transaccion_embedding = embedding_model.encode(descripcion)

        cuentas_similares = list(Cuenta.objects.filter(
            permite_movimientos=True
        ).order_by(
            L2Distance('embedding', transaccion_embedding)
        )[:5])

        if len(cuentas_similares) < 5:
            needed = 5 - len(cuentas_similares)
            excluded_ids = [c.id for c in cuentas_similares]
            adicionales = list(Cuenta.objects.exclude(id__in=excluded_ids).order_by(
                L2Distance('embedding', transaccion_embedding)
            )[:needed])
            cuentas_similares.extend(adicionales)


        cuenta_banco_default = Cuenta.objects.filter(nombre_cuenta__icontains="Bancos").first()
        id_banco = cuenta_banco_default.id if cuenta_banco_default else "BUSCAR_MANUALMENTE"
        nombre_banco = cuenta_banco_default.nombre_cuenta if cuenta_banco_default else "Bancos Generales"

        texto_cuentas_candidatas = "\n".join([
            f"- ID: {c.id}, Nombre: {c.nombre_cuenta} ({c.codigo_cuenta})"
            for c in cuentas_similares
        ])

        prompt = f"""
        Actúa como un contador experto. Tienes que generar un asiento contable balanceado para esta transacción.

        TRANSACCIÓN:
        - Descripción: "{descripcion}"
        - Monto Total: {monto}

        TUS HERRAMIENTAS (CATÁLOGO REDUCIDO):
        He buscado en la base de datos y estas son las cuentas más probables para clasificar la naturaleza del movimiento:
        {texto_cuentas_candidatas}

        REGLA DE CONTRAPARTIDA:
        - Asume que el dinero sale o entra a la cuenta de Tesorería/Bancos: (ID: {id_banco}, Nombre: {nombre_banco}).

        INSTRUCCIONES:
        1. Identifica si es INGRESO o GASTO/EGRESO.
        2. Selecciona la cuenta más apropiada de la lista de "Candidatas" para la naturaleza del movimiento.
        3. Genera el JSON con DOS líneas de detalle: una para la cuenta seleccionada y otra para el banco.

        FORMATO JSON ESPERADO (Estricto):
        {{
            "explicacion": "Breve justificación",
            "detalles": [
                {{
                    "cuenta_id": <ID_CUENTA_SELECCIONADA_DE_LISTA>,
                    "descripcion": "{descripcion}",
                    "debe": <MONTO si es gasto, 0 si es ingreso>,
                    "haber": <MONTO si es ingreso, 0 si es gasto>
                }},
                {{
                    "cuenta_id": {id_banco},
                    "descripcion": "Movimiento de banco",
                    "debe": <MONTO si es ingreso, 0 si es gasto>,
                    "haber": <MONTO si es gasto, 0 si es ingreso>
                }}
            ]
        }}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return response.text

    except Exception as e:
        print(f"Error clasificando: {e}")
        return None