import os
import time
import sys
import psycopg2  # Librería de PostgreSQL que ya tienes instalada

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_PORT = os.getenv('DB_PORT', 5432)


def wait_for_db(timeout=30):
    """Espera a que la base de datos esté disponible."""
    sys.stdout.write("Esperando conexión con PostgreSQL...")
    sys.stdout.flush()
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # Intenta hacer una conexión simple
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT
            )
            conn.close()
            sys.stdout.write("\n✅ PostgreSQL está listo.\n")
            sys.stdout.flush()
            return
        except psycopg2.OperationalError:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)

    sys.stderr.write(f"\n❌ Falló la conexión con PostgreSQL después de {timeout} segundos.\n")
    sys.stdout.flush()
    sys.exit(1)


if __name__ == '__main__':
    wait_for_db()