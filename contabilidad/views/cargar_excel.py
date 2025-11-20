import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models import TransaccionOriginal, ClasificacionLlm, Cuenta
from ..llm_service import clasificar_transaccion, get_embedding_model


class CargarExcelView(APIView):
    def post(self, request, *args, **kwargs):
        archivo_excel = request.FILES.get('file')

        if not archivo_excel:
            return Response({"error": "No se ha proporcionado ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(archivo_excel)
            df.dropna(subset=['Descripción', 'Monto'], inplace=True)

            model = get_embedding_model()
            transacciones_a_crear = []

            for index, row in df.iterrows():
                transaccion = TransaccionOriginal(
                    fecha=row['Fecha'],
                    descripcion=row['Descripción'],
                    monto=row['Monto'],
                    moneda=row.get('Moneda', 'USD'),
                    procesada=False,
                    archivo_origen=archivo_excel.name,
                    fila_origen=index + 2
                )
                transacciones_a_crear.append(transaccion)

            TransaccionOriginal.objects.bulk_create(transacciones_a_crear)

            descripciones = [t.descripcion for t in transacciones_a_crear]
            embeddings_de_transacciones = model.encode(descripciones,
                                                       show_progress_bar=True)

            clasificaciones_a_crear = []

            with ThreadPoolExecutor(max_workers=5) as executor:
                futuros = {
                    executor.submit(clasificar_transaccion, trans.descripcion, trans.monto, emb): trans
                    for trans, emb in zip(transacciones_a_crear, embeddings_de_transacciones)
                }

                for futuro in as_completed(futuros):
                    transaccion = futuros[futuro]
                    try:
                        resultado_json_raw = futuro.result()

                        if resultado_json_raw:
                            texto_limpio = resultado_json_raw.replace('```json', '').replace('```', '').strip()
                            datos_clasificacion = json.loads(texto_limpio)

                            detalles = datos_clasificacion.get('detalles', [])
                            explicacion = datos_clasificacion.get('explicacion', '')

                            cuenta_obj = None
                            tipo_inferido = 'PENDIENTE'

                            if detalles:
                                primer_detalle = detalles[0]
                                cuenta_id = primer_detalle.get('cuenta_id')

                                debe = float(primer_detalle.get('debe', 0))
                                if debe > 0:
                                    tipo_inferido = 'EGRESO'
                                else:
                                    tipo_inferido = 'INGRESO'

                                if cuenta_id and isinstance(cuenta_id, int):
                                    cuenta_obj = Cuenta.objects.filter(id=cuenta_id).first()

                            clasificaciones_a_crear.append(
                                ClasificacionLlm(
                                    transaccion_original=transaccion,
                                    tipo_transaccion=tipo_inferido,
                                    cuenta_sugerida=cuenta_obj,
                                    confianza=0.90,
                                    justificacion=explicacion,
                                    revisada=False
                                )
                            )

                    except Exception as exc:
                        print(f'La transacción {transaccion.id} generó un error de clasificación: {exc}')

            if clasificaciones_a_crear:
                ClasificacionLlm.objects.bulk_create(clasificaciones_a_crear)
            return Response({
                "mensaje": f"Se cargaron {len(transacciones_a_crear)} transacciones. {len(clasificaciones_a_crear)} fueron clasificadas por IA"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)