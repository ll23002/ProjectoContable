# contabilidad/views.py

import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import TransaccionOriginal, ClasificacionLlm, Categoria, Cuenta
from .llm_service import clasificar_transaccion, embedding_model


class CargarExcelView(APIView):
    def post(self, request, *args, **kwargs):
        archivo_excel = request.FILES.get('file')

        if not archivo_excel:
            return Response({"error": "No se ha proporcionado ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(archivo_excel)
            df.dropna(subset=['Descripción'], inplace=True)
            transacciones_a_crear = []
            for index, row in df.iterrows():
                transaccion = TransaccionOriginal(
                    fecha=row['Fecha'],
                    descripcion=row['Descripción'],
                    monto=row['Monto'],
                    moneda=row['Moneda'],
                    procesada=False,
                    archivo_origen=archivo_excel.name,
                    fila_origen=index + 2
                )
                transacciones_a_crear.append(transaccion)

            TransaccionOriginal.objects.bulk_create(transacciones_a_crear)

            descripciones = [t.descripcion for t in transacciones_a_crear]
            embeddings_de_transacciones = embedding_model.encode(descripciones, show_progress_bar=True)

            # --- PASO 2: Ejecución Concurrente de Llamadas a la API ---
            clasificaciones_a_crear = []

            # Usamos un ThreadPoolExecutor para hacer las llamadas en paralelo
            with ThreadPoolExecutor(max_workers=10) as executor:
                # Creamos un futuro para cada llamada a la API
                futuros = {
                    executor.submit(clasificar_transaccion, trans.descripcion, emb): trans
                    for trans, emb in zip(transacciones_a_crear, embeddings_de_transacciones)
                }

                # Procesamos los resultados a medida que van llegando
                for futuro in as_completed(futuros):
                    transaccion = futuros[futuro]
                    try:
                        resultado_json = futuro.result()
                        if resultado_json:
                            # La lógica de procesar cada resultado es la misma
                            datos_clasificacion = json.loads(resultado_json)
                            categoria_obj = None
                            cuenta_obj = None
                            sugerencia_cuenta_raw = datos_clasificacion.get('cuenta_sugerida', '')
                            if sugerencia_cuenta_raw:
                                codigo_limpio = re.sub(r'\D', '', sugerencia_cuenta_raw)
                                if codigo_limpio:
                                    try:
                                        cuenta_obj = Cuenta.objects.get(codigo_cuenta=codigo_limpio)
                                    except Cuenta.DoesNotExist:
                                        cuenta_obj = Cuenta.objects.filter(
                                            codigo_cuenta__startswith=codigo_limpio).first()

                            nombre_categoria = datos_clasificacion.get('categoria')
                            if nombre_categoria:
                                categoria_obj = Categoria.objects.filter(nombre__iexact=nombre_categoria).first()

                            # En lugar de crearla, la añadimos a una lista
                            clasificaciones_a_crear.append(
                                ClasificacionLlm(
                                    transaccion_original=transaccion,
                                    tipo_transaccion=datos_clasificacion.get('tipo_transaccion', '').upper(),
                                    categoria=categoria_obj,
                                    cuenta_sugerida=cuenta_obj,
                                    confianza=datos_clasificacion.get('confianza'),
                                    justificacion=datos_clasificacion.get('justificacion')
                                )
                            )
                            transaccion.procesada = True
                    except Exception as exc:
                        print(f'La transacción {transaccion.id} generó un error: {exc}')

            # --- PASO 3: Guardado Masivo en la Base de Datos ---
            if clasificaciones_a_crear:
                ClasificacionLlm.objects.bulk_create(clasificaciones_a_crear)

            # Actualizamos el estado 'procesada' de las transacciones que tuvieron éxito
            transacciones_exitosas = [c.transaccion_original for c in clasificaciones_a_crear]
            if transacciones_exitosas:
                TransaccionOriginal.objects.bulk_update(transacciones_exitosas, ['procesada'])

            return Response({"mensaje": f"Se procesaron {len(transacciones_a_crear)} transacciones exitosamente."},
                            status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)