import pandas as pd
from django.core.management.base import BaseCommand
from contabilidad.models import Cuenta, TipoCuenta
from django.utils import timezone


class Command(BaseCommand):
    """
    Comando para importar el catálogo de cuentas desde un archivo XLSX.

    Este comando procesa un archivo XLSX que contiene información sobre cuentas contables
    y las guarda en la base de datos, asignándoles su tipo, nivel y jerarquía.
    """
    help = 'Importa el catálogo de cuentas desde un archivo XLSX.'

    def add_arguments(self, parser):
        """
        Agrega los argumentos necesarios para ejecutar el comando.

        Args:
            parser (ArgumentParser): El analizador de argumentos para el comando.
        """
        parser.add_argument('file_path', type=str, help='La ruta del archivo XLSX a importar.')

    def handle(self, *args, **kwargs):
        """
        Ejecuta el comando para importar las cuentas desde el archivo XLSX.

        Args:
            *args: Argumentos posicionales.
            **kwargs: Argumentos con nombre, incluyendo la ruta del archivo.

        Returns:
            None
        """
        file_path = kwargs['file_path']
        self.stdout.write(self.style.SUCCESS(f'Iniciando la importación desde "{file_path}"...'))

        try:
            df = pd.read_excel(file_path)
            df.dropna(subset=['CODIGO', 'DESCRIPCIÓN'], inplace=True)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: El archivo no fue encontrado.'))
            return

        df['CODIGO_LIMPIO'] = df['CODIGO'].astype(str).apply(lambda x: x.split('-')[0].strip())
        df['codigo_len'] = df['CODIGO_LIMPIO'].str.len()
        df = df.sort_values(by='codigo_len').reset_index(drop=True)

        tipos_base = {
            '1': ('ACTIVO', 'DEUDORA'),
            '2': ('PASIVO', 'ACREEDORA'),
            '3': ('PATRIMONIO', 'ACREEDORA'),
            '4': ('INGRESO', 'ACREEDORA'),
            '5': ('EGRESO', 'DEUDORA'),
            '6': ('CUENTAS LIQUIDADORAS', 'DEUDORA'),
            '7': ('CUENTAS DE ORDEN', 'DEUDORA')
        }

        for codigo, (nombre, naturaleza) in tipos_base.items():
            TipoCuenta.objects.get_or_create(
                nombre_tipo=nombre,
                defaults={'naturaleza': naturaleza}
            )

        for index, row in df.iterrows():
            codigo = row['CODIGO_LIMPIO']
            nombre = row['DESCRIPCIÓN']

            if not codigo:
                continue

            primer_digito = codigo[0]
            try:
                nombre_tipo_a_buscar = tipos_base[primer_digito][0]
                tipo_cuenta_obj = TipoCuenta.objects.get(nombre_tipo=nombre_tipo_a_buscar)
            except (KeyError, TipoCuenta.DoesNotExist):
                self.stdout.write(
                    self.style.WARNING(f'ADVERTENCIA: Tipo de cuenta desconocido para código "{codigo}". Omitiendo.'))
                continue

            longitud = len(codigo)
            if longitud <= 2:
                nivel = 1
            elif longitud <= 4:
                nivel = 2
            else:
                nivel = 3

            parent_obj = None
            if nivel > 1:
                parent_codigo = None
                if longitud == 2:
                    parent_codigo = codigo[:1]
                elif longitud == 4:
                    parent_codigo = codigo[:2]
                elif longitud == 6:
                    parent_codigo = codigo[:4]
                elif longitud == 8:
                    parent_codigo = codigo[:6]

                if parent_codigo:
                    try:
                        parent_obj = Cuenta.objects.get(codigo_cuenta=parent_codigo)
                    except Cuenta.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'ADVERTENCIA: Padre "{parent_codigo}" no encontrado para cuenta "{codigo}".'))

            cuenta, created = Cuenta.objects.update_or_create(
                codigo_cuenta=codigo,
                defaults={
                    'nombre_cuenta': nombre,
                    'descripcion': nombre,
                    'tipo_cuenta': tipo_cuenta_obj,
                    'permite_movimientos': True
              
                }
            )

            if created:
                self.stdout.write(f'  -> Creada: [{cuenta.codigo_cuenta}] {cuenta.nombre_cuenta}')
            else:
                self.stdout.write(f'  -> Actualizada: [{cuenta.codigo_cuenta}] {cuenta.nombre_cuenta}')

            if parent_obj:
                if not cuenta.permite_movimientos:
                    cuenta.permite_movimientos = True
                    cuenta.save()

                if parent_obj.permite_movimientos:
                    parent_obj.permite_movimientos = False
                    parent_obj.save()

        self.stdout.write(self.style.SUCCESS('¡Importación completada exitosamente!'))