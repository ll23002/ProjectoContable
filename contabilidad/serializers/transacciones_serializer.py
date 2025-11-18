from rest_framework import serializers
from ..models import TransaccionOriginal

class TransaccionOriginalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransaccionOriginal
        fields = '__all__'