import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


def clasificar_transaccion(descripcion: str):
    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY o GOOGLE_API_KEY en el archivo .env")

        client = genai.Client(api_key=api_key)

        prompt = f"""
        Analiza la siguiente transacción contable de El Salvador y clasifícala.
        Descripción de la transacción: "{descripcion}"

        Devuelve únicamente un objeto JSON válido con la siguiente estructura exacta:
        {{
          "tipo_transaccion": "INGRESO" o "EGRESO",
          "categoria": "el nombre de la categoría contable más apropiada",
          "cuenta_sugerida": "el código de la cuenta contable más relevante",
          "confianza": un número decimal entre 0.0 y 1.0 que represente tu confianza en la clasificación,
          "justificacion": "una explicación breve de por qué elegiste esa categoría y cuenta"
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
        print(f"Error al conectar con la API de Gemini: {e}")
        return None