from rest_framework import serializers
from ..models import TransaccionOriginal, ClasificacionLlm

class ClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClasificacionLlm
        fields = ['id', 'tipo_transaccion', 'cuenta_sugerida', 'justificacion', 'confianza']

class TransaccionOriginalSerializer(serializers.ModelSerializer):
    clasificacion = serializers.SerializerMethodField()

    class Meta:
        model = TransaccionOriginal
        fields = '__all__'

    def get_clasificacion(self, obj):
        sugerencia = obj.clasificacionllm_set.last()

        if sugerencia:
            return ClasificacionSerializer(sugerencia).data
        return None