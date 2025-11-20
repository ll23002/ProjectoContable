from rest_framework import serializers
from ..models import TransaccionOriginal, ClasificacionLlm


# 1. Agregamos primero el serializer para la Clasificación (La "Sugerencia")
class ClasificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClasificacionLlm
        # Estos son los campos que tu JS va a leer (sugerencia.cuenta_sugerida, sugerencia.justificacion, etc.)
        fields = ['id', 'tipo_transaccion', 'cuenta_sugerida', 'justificacion', 'confianza']


# 2. Modificamos el serializer de la Transacción para inyectarle la clasificación
class TransaccionOriginalSerializer(serializers.ModelSerializer):
    # Aquí definimos el campo "mágico" que no existe en la tabla TransaccionOriginal,
    # pero que queremos enviar al frontend.
    clasificacion = serializers.SerializerMethodField()

    class Meta:
        model = TransaccionOriginal
        # Al usar __all__, DRF incluirá todos los campos del modelo MÁS el campo 'clasificacion' que definimos arriba.
        fields = '__all__'

    def get_clasificacion(self, obj):
        """
        Este método busca si existe alguna clasificación de IA asociada a esta transacción.
        Django crea automáticamente la relación inversa 'clasificacionllm_set'.
        """
        # Tomamos la última (.last()) por si acaso corriste el proceso varias veces, nos quedamos con la más reciente.
        sugerencia = obj.clasificacionllm_set.last()

        if sugerencia:
            # Si existe, la serializamos y devolvemos el JSON
            return ClasificacionSerializer(sugerencia).data
        return None