from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import AsientoContable
from ..models import DetalleAsiento
from ..models import Cuenta
from ..models import TransaccionOriginal
import datetime
from django.db import transaction
from django.utils import timezone


class AsientosView(APIView):

    def post(self, request):
        # 1. Obtener datos
        numero_asiento = request.data.get('numero_asiento')
        transaccion_original_id = request.data.get('transaccion')  # <--- ESTE ES EL Eslabón Perdido
        fecha_str = request.data.get('fecha')
        detalles = request.data.get('detalles')

        # 2. Validaciones básicas
        if not detalles or len(detalles) == 0:
            return Response({"error": "Debe incluir al menos un detalle"}, status=400)

        try:
            fecha = datetime.datetime.fromisoformat(fecha_str).date()
        except (ValueError, TypeError):
            return Response({"error": "La fecha no tiene formato válido ISO8601 (YYYY-MM-DD)"}, status=400)

        # 3. Validar Transacción Original
        transaccion_original_obj = None
        if transaccion_original_id:
            try:
                transaccion_original_obj = TransaccionOriginal.objects.get(id=transaccion_original_id)
                # Opcional: Verificar si ya estaba procesada
                # if transaccion_original_obj.procesada:
                #     return Response({"error": "Esta transacción ya fue contabilizada"}, status=400)
            except TransaccionOriginal.DoesNotExist:
                return Response({"error": "transaccion_original_id no existe"}, status=400)

        # 4. Validar Balance (Debe == Haber)
        total_debe = 0
        total_haber = 0

        for detalle in detalles:
            debe = float(detalle.get('debe', 0))
            haber = float(detalle.get('haber', 0))

            if debe > 0 and haber > 0:
                return Response({"error": "Un detalle no puede tener debe y haber > 0 a la vez"}, status=400)

            total_debe += debe
            total_haber += haber

        # Usamos round para evitar errores de punto flotante (ej: 100.00000001 vs 100)
        if round(total_debe, 2) != round(total_haber, 2):
            return Response({
                "error": f"El asiento no está balanceado. Debe: {total_debe}, Haber: {total_haber}"
            }, status=400)

        # 5. Guardado Atómico
        with transaction.atomic():

            # A. Crear el Asiento Contable
            asiento = AsientoContable.objects.create(
                numero_asiento=numero_asiento,
                fecha=fecha,
                transaccion_original=transaccion_original_obj,
                total_debe=total_debe,
                total_haber=total_haber,
                balanceado=True,
                created_at=timezone.now()
            )

            # B. Crear los Detalles
            detalles_a_insertar = []
            for idx, detalle in enumerate(detalles, start=1):
                cuenta_id = detalle.get('cuenta_id')
                try:
                    cuenta_obj = Cuenta.objects.get(id=cuenta_id)
                except Cuenta.DoesNotExist:
                    raise Exception(f"La cuenta con id {cuenta_id} no existe")  # Esto hace rollback automático

                detalles_a_insertar.append(
                    DetalleAsiento(
                        asiento_contable=asiento,
                        cuenta=cuenta_obj,
                        descripcion=detalle.get('descripcion'),
                        debe=detalle.get('debe', 0),
                        haber=detalle.get('haber', 0),
                        orden=idx,
                        created_at=timezone.now()
                    )
                )

            DetalleAsiento.objects.bulk_create(detalles_a_insertar)

            # C. IMPORTANTE: Marcar la transacción original como procesada
            if transaccion_original_obj:
                transaccion_original_obj.procesada = True  # <--- AQUÍ ESTÁ LA MAGIA
                transaccion_original_obj.save()

        return Response({
            "id": asiento.id,
            "mensaje": "Asiento creado y transacción marcada como procesada",
            "numero_asiento": asiento.numero_asiento,
            "fecha": asiento.fecha.isoformat(),
            "total_debe": str(asiento.total_debe),
            "total_haber": str(asiento.total_haber)
        }, status=201)