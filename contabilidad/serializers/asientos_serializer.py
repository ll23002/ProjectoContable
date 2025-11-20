from rest_framework import serializers
from ..models import AsientoContable, DetalleAsiento

class DetalleAsientoSerializer(serializers.ModelSerializer):
    nombre_cuenta = serializers.CharField(source='cuenta.nombre_cuenta', read_only=True)
    codigo_cuenta = serializers.CharField(source='cuenta.codigo_cuenta', read_only=True)

    class Meta:
        model = DetalleAsiento
        fields = ['id', 'cuenta', 'nombre_cuenta', 'codigo_cuenta', 'descripcion', 'debe', 'haber']

class AsientoContableSerializer(serializers.ModelSerializer):
    detalles = DetalleAsientoSerializer(many=True, read_only=True, source='detalleasiento_set')

    class Meta:
        model = AsientoContable
        fields = ['id', 'numero_asiento', 'fecha', 'total_debe', 'total_haber', 'detalles']