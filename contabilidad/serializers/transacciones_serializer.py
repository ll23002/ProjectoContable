from rest_framework import serializers
from ..models import TransaccionOriginal, ClasificacionLlm, Cuenta
from django.db.models import Prefetch


class TransaccionOriginalSerializer(serializers.ModelSerializer):
    # 1. Campos derivados (SerializerMethodField) que el frontend espera
    clasificacion_tipo = serializers.SerializerMethodField()
    clasificacion_cuenta = serializers.SerializerMethodField()
    debe = serializers.SerializerMethodField()
    haber = serializers.SerializerMethodField()

    class Meta:
        model = TransaccionOriginal
        # CORRECCIÓN: Se listan explícitamente todos los campos del modelo base
        # más los campos derivados para evitar el TypeError.
        fields = (
            'id',
            'fecha',
            'descripcion',
            'monto',
            'moneda',
            'archivo_origen',
            'fila_origen',
            'procesada',
            'created_at',
            # Campos de Clasificación / Contabilidad esperados por el frontend
            'clasificacion_tipo',
            'clasificacion_cuenta',
            'debe',
            'haber',
        )

    def get_clasificacion_llm(self, obj: TransaccionOriginal):
        """
        Busca y retorna la clasificación LLM asociada a la transacción.
        Se usa select_related para optimizar la búsqueda de la cuenta.
        Se usa .first() para evitar errores si la relación inversa no existe.
        """
        try:
            # Usar 'clasificacionllm_set' (relación inversa por defecto)
            return obj.clasificacionllm_set.select_related('cuenta_sugerida').first()
        except Exception:
            return None

    def get_clasificacion_tipo(self, obj: TransaccionOriginal):
        """Retorna el tipo de transacción (INGRESO o EGRESO)."""
        clasificacion = self.get_clasificacion_llm(obj)
        return clasificacion.tipo_transaccion if clasificacion else None

    def get_clasificacion_cuenta(self, obj: TransaccionOriginal):
        """
        Retorna la cuenta sugerida en formato 'CÓDIGO - NOMBRE' para reportes.
        (Ej: '4101 - Ventas').
        """
        clasificacion = self.get_clasificacion_llm(obj)
        if clasificacion and clasificacion.cuenta_sugerida:
            # El frontend espera este formato para el Libro Diario/Mayor
            return f"{clasificacion.cuenta_sugerida.codigo_cuenta} - {clasificacion.cuenta_sugerida.nombre_cuenta}"
        return None

    def get_debe(self, obj: TransaccionOriginal):
        """
        Calcula el monto del DEBE. Si la clasificación es EGRESO, el monto va al Debe;
        en caso contrario, es 0.00 (partida simple para reportes).
        """
        clasificacion = self.get_clasificacion_llm(obj)
        if clasificacion and clasificacion.tipo_transaccion == 'EGRESO':
            return obj.monto
        return 0.00

    def get_haber(self, obj: TransaccionOriginal):
        """
        Calcula el monto del HABER. Si la clasificación es INGRESO, el monto va al Haber;
        en caso contrario, es 0.00.
        """
        clasificacion = self.get_clasificacion_llm(obj)
        if clasificacion and clasificacion.tipo_transaccion == 'INGRESO':
            return obj.monto
        return 0.00