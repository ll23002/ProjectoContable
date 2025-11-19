from django.core.management.base import BaseCommand
from contabilidad.models import Cuenta
from sentence_transformers import SentenceTransformer


class Command(BaseCommand):
    """
    Comando para generar y guardar los embeddings para todas las cuentas del catálogo.

    Este comando utiliza un modelo de SentenceTransformer para generar embeddings
    basados en las descripciones de las cuentas y los guarda en la base de datos.
    """
    help = 'Genera y guarda los embeddings para todas las cuentas del catálogo.'

    def handle(self, *args, **kwargs):
        """
        Ejecuta el comando para generar los embeddings.

        Este método carga el modelo de SentenceTransformer, genera los embeddings
        para las cuentas existentes y los guarda en la base de datos.

        Args:
            *args: Argumentos posicionales.
            **kwargs: Argumentos con nombre.

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS('Iniciando la generación de embeddings...'))

        self.stdout.write('Cargando modelo liviano...')
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', trust_remote_code=True)
        self.stdout.write(self.style.SUCCESS('¡Modelo cargado!'))

        cuentas = Cuenta.objects.all()

        textos_a_codificar = [
            f"{cuenta.codigo_cuenta} - {cuenta.nombre_cuenta}: {cuenta.descripcion or ''}"
            for cuenta in cuentas
        ]

        if not textos_a_codificar:
            self.stdout.write(self.style.WARNING('No se encontraron cuentas para procesar.'))
            return

        self.stdout.write(f'Codificando {len(textos_a_codificar)} cuentas...')

        embeddings = model.encode(textos_a_codificar, show_progress_bar=True, task ='retrieval')

        self.stdout.write('Guardando los embeddings en la base de datos...')

        for i, cuenta in enumerate(cuentas):
            cuenta.embedding = embeddings[i]

        Cuenta.objects.bulk_update(cuentas, ['embedding'])

        self.stdout.write(self.style.SUCCESS(f'¡Proceso completado! Se actualizaron {len(cuentas)} cuentas.'))