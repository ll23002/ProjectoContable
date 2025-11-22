# This is an auto-generated Backend model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Backend to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from pgvector.django import VectorField


class AsientoContable(models.Model):
    numero_asiento = models.CharField(unique=True, max_length=20)
    fecha = models.DateField()
    #descripcion = models.TextField()
    #referencia = models.CharField(max_length=100, blank=True, null=True)
    transaccion_original = models.ForeignKey('TransaccionOriginal', on_delete=models.CASCADE, blank=True, null=True)
    total_debe = models.DecimalField(max_digits=15, decimal_places=2)
    total_haber = models.DecimalField(max_digits=15, decimal_places=2)
    balanceado = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'asiento_contable'


class Auditoria(models.Model):
    tabla = models.CharField(max_length=50)
    registro_id = models.IntegerField()
    accion = models.CharField(max_length=20)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'auditoria'



class ClasificacionLlm(models.Model):
    transaccion_original = models.ForeignKey('TransaccionOriginal', on_delete=models.CASCADE)
    tipo_transaccion = models.CharField(max_length=20)
    cuenta_sugerida = models.ForeignKey('Cuenta', on_delete=models.CASCADE, blank=True, null=True)
    confianza = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    justificacion = models.TextField(blank=True, null=True)
    revisada = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'clasificacion_llm'

class Cuenta(models.Model):
    codigo_cuenta = models.CharField(unique=True, max_length=20)
    nombre_cuenta = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo_cuenta = models.ForeignKey('TipoCuenta', on_delete=models.CASCADE)
    permite_movimientos = models.BooleanField(default=True)
    embedding = VectorField(dimensions=384, blank=True, null=True)
    class Meta:
        db_table = 'cuenta'


class DetalleAsiento(models.Model):
    asiento_contable = models.ForeignKey(AsientoContable, on_delete=models.CASCADE)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True)
    debe = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    haber = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    orden = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'detalle_asiento'


class PeriodoContable(models.Model):
    nombre = models.CharField(max_length=50)
    tipo_periodo = models.CharField(max_length=20)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    año = models.IntegerField()
    mes = models.IntegerField(blank=True, null=True)
    trimestre = models.IntegerField(blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True)
    cerrado = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'periodo_contable'


class TipoCuenta(models.Model):
    nombre_tipo = models.CharField(unique=True, max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    naturaleza = models.CharField(max_length=10)

    class Meta:
        db_table = 'tipo_cuenta'


class TransaccionOriginal(models.Model):
    fecha = models.DateField()
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    moneda = models.CharField(max_length=5)
    archivo_origen = models.CharField(max_length=255, blank=True, null=True)
    fila_origen = models.IntegerField(blank=True, null=True)
    procesada = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'transaccion_original'
