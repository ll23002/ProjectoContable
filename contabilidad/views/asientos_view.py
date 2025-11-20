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

from ..serializers.asientos_serializer import AsientoContableSerializer


class AsientosView(APIView):
    def post(self, request):
        numero_asiento = request.data.get('numero_asiento')
        transaccion_original_id = request.data.get('transaccion')
        fecha_str = request.data.get('fecha')
        detalles = request.data.get('detalles')

        if not detalles or len(detalles) == 0:
            return Response({"error": "Debe incluir al menos un detalle"}, status=400)

        try:
            fecha = datetime.datetime.fromisoformat(fecha_str).date()
        except (ValueError, TypeError):
            return Response({"error": "La fecha no tiene formato válido"}, status=400)

        transaccion_original_obj = None
        if transaccion_original_id:
            try:
                transaccion_original_obj = TransaccionOriginal.objects.get(id=transaccion_original_id)
            except TransaccionOriginal.DoesNotExist:
                return Response({"error": "transaccion_original_id no existe"}, status=400)

        total_debe = 0
        total_haber = 0

        for detalle in detalles:
            debe = float(detalle.get('debe', 0))
            haber = float(detalle.get('haber', 0))

            if debe > 0 and haber > 0:
                return Response({"error": "Un detalle no puede tener debe y haber > 0 a la vez"}, status=400)

            total_debe += debe
            total_haber += haber

        if round(total_debe, 2) != round(total_haber, 2):
            return Response({
                "error": f"El asiento no está balanceado. Debe: {total_debe}, Haber: {total_haber}"
            }, status=400)

        with transaction.atomic():
            asiento = AsientoContable.objects.create(
                numero_asiento=numero_asiento,
                fecha=fecha,
                transaccion_original=transaccion_original_obj,
                total_debe=total_debe,
                total_haber=total_haber,
                balanceado=True,
                created_at=timezone.now()
            )

            detalles_a_insertar = []
            for idx, detalle in enumerate(detalles, start=1):
                cuenta_id = detalle.get('cuenta_id')
                try:
                    cuenta_obj = Cuenta.objects.get(id=cuenta_id)
                except Cuenta.DoesNotExist:
                    raise Exception(f"La cuenta con id {cuenta_id} no existe")

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

            if transaccion_original_obj:
                transaccion_original_obj.procesada = True
                transaccion_original_obj.save()

        return Response({
            "id": asiento.id,
            "mensaje": "Asiento creado y transacción marcada como procesada",
            "numero_asiento": asiento.numero_asiento,
            "fecha": asiento.fecha.isoformat(),
            "total_debe": str(asiento.total_debe),
            "total_haber": str(asiento.total_haber)
        }, status=201)

    def get(self, request):
        asientos = AsientoContable.objects.all().order_by('fecha', 'numero_asiento').prefetch_related(
            'detalleasiento_set__cuenta')
        serializer = AsientoContableSerializer(asientos, many=True)
        return Response(serializer.data)