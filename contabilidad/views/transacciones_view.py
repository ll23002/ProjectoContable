from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import TransaccionOriginal
from ..serializers.transacciones_serializer import TransaccionOriginalSerializer
from rest_framework.viewsets import ModelViewSet

class TransaccionesViewSet(ModelViewSet):
    queryset = TransaccionOriginal.objects.all()
    serializer_class = TransaccionOriginalSerializer