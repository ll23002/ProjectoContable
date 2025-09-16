# contabilidad/management/commands/generar_embeddings.py

from django.core.management.base import BaseCommand
from contabilidad.models import Cuenta
from sentence_transformers import SentenceTransformer
import numpy as np


class Command(BaseCommand):
    help = 'Genera y guarda los embeddings para todas las cuentas del catálogo.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando la generación de embeddings...'))

        # 1. Cargar el modelo de embeddings pre-entrenado.
        #    La primera vez que se ejecute, descargará el modelo (puede tardar un poco).
        #    'all-MiniLM-L6-v2' es un modelo excelente y ligero (384 dimensiones).
        self.stdout.write('Cargando el modelo de SentenceTransformer...')
        model = SentenceTransformer('all-MiniLM-L6-v2')
        self.stdout.write(self.style.SUCCESS('¡Modelo cargado!'))

        # 2. Obtener todas las cuentas de la base de datos.
        cuentas = Cuenta.objects.all()

        # Preparamos los textos que vamos a convertir a vectores.
        # Combinamos el código, nombre y descripción para darle más contexto al modelo.
        textos_a_codificar = [
            f"{cuenta.codigo_cuenta} - {cuenta.nombre_cuenta}: {cuenta.descripcion or ''}"
            for cuenta in cuentas
        ]

        if not textos_a_codificar:
            self.stdout.write(self.style.WARNING('No se encontraron cuentas para procesar.'))
            return

        self.stdout.write(f'Codificando {len(textos_a_codificar)} cuentas...')

        # 3. Generar todos los embeddings en un solo lote (mucho más rápido).
        embeddings = model.encode(textos_a_codificar, show_progress_bar=True)

        self.stdout.write('Guardando los embeddings en la base de datos...')

        # 4. Guardar cada embedding en su cuenta correspondiente.
        for i, cuenta in enumerate(cuentas):
            cuenta.embedding = embeddings[i]

        # Usamos bulk_update para guardar todos los cambios en una sola consulta (eficiente).
        Cuenta.objects.bulk_update(cuentas, ['embedding'])

        self.stdout.write(self.style.SUCCESS(f'¡Proceso completado! Se actualizaron {len(cuentas)} cuentas.'))