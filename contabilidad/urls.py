from django.urls import path
from .views import CargarExcelView

urlpatterns = [path('cargar-excel/', CargarExcelView.as_view(), name='cargar_excel')]