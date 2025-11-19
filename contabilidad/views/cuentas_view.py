
from ..models import Cuenta
from ..serializers.cuentas_serializer import CuentaSerializer
from rest_framework.viewsets import ModelViewSet

class CuentasViewSet(ModelViewSet):
    queryset = Cuenta.objects.all()
    serializer_class = CuentaSerializer
    http_method_names = ['get']