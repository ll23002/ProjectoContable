
from ..models import Cuenta
from ..serializers.cuentas_serializer import CuentaSerializer
from rest_framework.viewsets import ModelViewSet

class CuentasViewSet(ModelViewSet):
    """
    Expose only accounts that allow movements (cuentas hijas) so the frontend
    can use them when creating accounting entries. Parent accounts (permite_movimientos=False)
    are intentionally excluded to prevent users from selecting them when contabilizing.
    """
    queryset = Cuenta.objects.filter(permite_movimientos=True)
    serializer_class = CuentaSerializer
    http_method_names = ['get']