import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from .models import TransaccionOriginal, ClasificacionLlm, Categoria, Cuenta
from .llm_service import clasificar_transaccion


class CargarExcelView(APIView):
    """
    Esta vista permite cargar un archivo Excel, leer sus filas y procesar cada transacción
    utilizando un modelo LLM para clasificarla automáticamente.
    """

    def post(self, request, *args, **kwargs):
        """
        Maneja la solicitud POST para cargar y procesar un archivo Excel.

        Args:
            request (Request): La solicitud HTTP que contiene el archivo Excel.
        Returns:
            Response: Una respuesta HTTP con el resultado del procesamiento.
        Raises:
            Exception: Si ocurre un error durante el procesamiento del archivo.
        """
        archivo_excel = request.FILES.get('file')

        if not archivo_excel:
            return Response({"error": "No se ha proporcionado ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(archivo_excel)

            for index, row in df.iterrows():
                transaccion = TransaccionOriginal.objects.create(
                    fecha=row['Fecha'],
                    descripcion=row['Descripción'],
                    monto=row['Monto'],
                    moneda=row['Moneda'],
                    procesada=False,
                    archivo_origen=archivo_excel.name,
                    fila_origen=index + 2
                )

                resultado_json = clasificar_transaccion(transaccion.descripcion)

                if resultado_json:
                    datos_clasificacion = json.loads(resultado_json)

                    categoria_obj = None
                    cuenta_obj = None

                    try:
                        nombre_categoria = datos_clasificacion.get('categoria')
                        if nombre_categoria:
                            categoria_obj = Categoria.objects.filter(nombre__iexact=nombre_categoria).first()
                    except Categoria.DoesNotExist:
                        print(f"La categoría '{nombre_categoria}' sugerida por el LLM no existe.")

                    try:
                        codigo_cuenta = datos_clasificacion.get('cuenta_sugerida')
                        if codigo_cuenta:
                            cuenta_obj = Cuenta.objects.get(codigo_cuenta=codigo_cuenta)
                    except Cuenta.DoesNotExist:
                        print(f"La cuenta '{codigo_cuenta}' sugerida por el LLM no existe.")

                    ClasificacionLlm.objects.create(
                        transaccion_original=transaccion,
                        tipo_transaccion=datos_clasificacion.get('tipo_transaccion', '').upper(),
                        categoria=categoria_obj,
                        cuenta_sugerida=cuenta_obj,
                        confianza=datos_clasificacion.get('confianza'),
                        justificacion=datos_clasificacion.get('justificacion')
                    )
                    transaccion.procesada = True
                    transaccion.save()

            return Response({"mensaje": "Datos cargados y clasificados exitosamente."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)