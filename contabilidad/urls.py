from django.urls import path, include
from .views.cargar_excel import CargarExcelView
from rest_framework.routers import DefaultRouter
from .views.transacciones_view import TransaccionesViewSet
from .views.cuentas_view import CuentasViewSet
from .views.asientos_view import AsientosView

router = DefaultRouter()

# El router de Django maneja las rutas para el ViewSet automáticamente, define la ruta base como "transacciones"
# El router generará las rutas para las operaciones CRUD, esto es por el ModelViewSet.
router.register(r'transacciones', TransaccionesViewSet)
router.register(r'cuentas', CuentasViewSet)


urlpatterns = [
    path('cargar-excel/', CargarExcelView.as_view(), name='cargar_excel'),
    path('asiento-contable/', AsientosView.as_view(), name='asiento-contable'),
    path('', include(router.urls)),
]