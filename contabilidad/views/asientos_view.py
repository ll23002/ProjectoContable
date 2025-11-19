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
from django.db.models import Max
from datetime import date




class AsientosView(APIView):

    def _generar_numero_asiento(fecha: date) -> str:
        año_actual = fecha.year
        prefijo = f"{año_actual}"

        ultimo_asiento = AsientoContable.objects.filter(
            numero_asiento__startswith=prefijo
        ).aggregate(
            max_num=Max('numero_asiento')
        )['max_num']

        if ultimo_asiento:
            try:
                ultimo_consecutivo = int(ultimo_asiento.split('-')[-1])
            except (ValueError, IndexError):
                ultimo_consecutivo = 0
        else:
            ultimo_consecutivo = 0

        nuevo_consecutivo = ultimo_consecutivo + 1
        nuevo_numero_asiento = f"{prefijo}-{str(nuevo_consecutivo).zfill(5)}"

        return nuevo_numero_asiento






    def post(self, request):
        transaccion_original_id = request.data.get('transaccion')
        fecha = datetime.datetime.today().date()
        detalles = request.data.get('detalles')
        try:
            numero_asiento = self._generar_numero_asiento(fecha)
        except Exception as e:
            return Response({"error": f"Error al generar el número de asiento: {e}"}, status=500)


        if not detalles or len(detalles) == 0:
            return Response({"error": "Debe incluir al menos un detalle"}, status=400)

        try:
            fecha = datetime.datetime.fromisoformat(fecha).date()
        except:
            return Response({"error": "La fecha no tiene formato válido ISO8601"}, status=400)

     
        transaccion_original_obj = None
        if transaccion_original_id:
            try:
                transaccion_original_obj = TransaccionOriginal.objects.get(id=transaccion_original_id)
            except TransaccionOriginal.DoesNotExist:
                return Response({"error": "transaccion_original_id no existe"}, status=400)

       
        total_debe = 0
        total_haber = 0

        for detalle in detalles:

            # Validar debe/haber
            debe = detalle.get('debe', 0)
            haber = detalle.get('haber', 0)

            if (debe is None or haber is None):
                return Response({"error": "Todos los detalles deben incluir debe y haber"}, status=400)

            if debe > 0 and haber > 0:
                return Response({"error": "Un detalle no puede tener debe y haber > 0 a la vez"}, status=400)

            if debe == 0 and haber == 0:
                return Response({"error": "Un detalle no puede tener debe y haber ambos en cero"}, status=400)

            total_debe += debe
            total_haber += haber

        if total_debe != total_haber:
            return Response({"error": "El asiento no está balanceado"}, status=400)

    
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
                    return Response({"error": f"La cuenta con id {cuenta_id} no existe"}, status=400)

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

        return Response({
            "id": asiento.id,
            "numero_asiento": asiento.numero_asiento,
            "fecha": asiento.fecha.isoformat(),
            "total_debe": str(asiento.total_debe),
            "total_haber": str(asiento.total_haber),
            "balanceado": asiento.balanceado,
            "detalles_insertados": len(detalles_a_insertar)
        }, status=201)
