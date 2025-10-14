## 🚀 Instalación


**Preparar PostgreSQL con pgvector**

**Docker**
```yaml
# docker-compose.yml
services:
  db16:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_PASSWORD: 12345678
    ports:
      - "5432:5432"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./init:/docker-entrypoint-initdb.d


  pgadmin4_16:
    image: dpage/pgadmin4
    container_name: ProyectoContable_db16
    environment:
      PGADMIN_DEFAULT_EMAIL: usuario@ues.edu.sv
      PGADMIN_DEFAULT_PASSWORD: 12345678
      PGADMIN_LISTEN_PORT: 5050
    ports:
      - "5050:5050"
    depends_on:
      - db16

```

## Descripción General

Este sistema contable está diseñado para automatizar la clasificación de transacciones financieras utilizando una arquitectura de **Inteligencia Artificial de última generación**. Permite:

- ✅ **Cargar transacciones masivamente** desde archivos Excel
- 🧠 **Clasificar cuentas con alta precisión** usando un modelo de **Búsqueda Aumentada por Generación (RAG)**, que combina búsqueda semántica vectorial con un LLM (Gemini 2.5)
- ✏️ **Supervisión y corrección humana** de las clasificaciones automáticas
- 📈 **Generar reportes contables** para análisis
- ⚖️ **Verificar balances automáticamente**


### **RAG = Retrieval-Augmented Generation (Búsqueda Aumentada por Generación)**

En lugar de que el LLM adivine la cuenta correcta entre cientos de opciones:

1. 🔍 **Retrieval**: Busca semánticamente las 5 cuentas más similares
2. 🧠 **Augmentation**: Le da al LLM solo esas 5 opciones
3. ⚡ **Generation**: El LLM elige la mejor de las 5

**Resultado**: Mayor precisión, menor costo, respuestas más rápidas.

---

## Preparación del Entorno

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar la Base de Datos (Primera Vez)
El sistema requiere la extensión **pgvector** en PostgreSQL.

```sql
-- Ejecutar en pgAdmin una sola vez
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Cargar Datos Maestros (Primera Vez)
Para que el sistema funcione, necesita el catálogo de cuentas y su mapa semántico:

```bash
# 1. Cargar el catálogo de cuentas desde tu archivo Excel
python manage.py importar_cuentas ruta/archivo.xlsx

# 2. Generar los embeddings (mapa semántico) para las cuentas cargadas
python manage.py generar_embeddings
```

---

## Tablas del Sistema

### 📊 1. `tipo_cuenta`
**Propósito**: Define los tipos básicos de cuentas contables según principios contables.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `nombre_tipo` | VARCHAR(50) | Nombre del tipo (ACTIVO, PASIVO, etc.) |
| `descripcion` | TEXT | Descripción detallada |
| `naturaleza` | VARCHAR(10) | DEUDORA o ACREEDORA |

**Datos iniciales**:
- ACTIVO (DEUDORA) - Recursos de la empresa
- PASIVO (ACREEDORA) - Obligaciones de la empresa
- PATRIMONIO (ACREEDORA) - Capital y utilidades
- INGRESO (ACREEDORA) - Ingresos por ventas/servicios
- EGRESO (DEUDORA) - Gastos operativos

---

### 2. `cuenta` ⭐ **CON EMBEDDINGS**
**Propósito**: Catálogo completo de cuentas contables, **enriquecido con representación semántica** para búsquedas inteligentes.

| Campo | Tipo             | Descripción |
|-------|------------------|-------------|
| `id` | SERIAL           | ID único automático |
| `codigo_cuenta` | VARCHAR(20)      | Código contable (ej: 1101) |
| `nombre_cuenta` | VARCHAR(200)     | Nombre de la cuenta |
| `descripcion` | TEXT             | Descripción detallada |
| `tipo_cuenta_id` | INTEGER          | FK a `tipo_cuenta` |
| `embedding` | **VECTOR(2048)** | 🧠 **Vector semántico que representa el significado de la cuenta** |

**Campo `embedding`**
- **Tipo**: `VECTOR(2048)` - Vector matemático de 2048 dimensiones
- **Propósito**: Representa el "significado" de la cuenta en forma matemática
- **Generación**: Se crea automáticamente con `python manage.py generar_embeddings`
- **Uso**: Permite búsquedas semánticas súper rápidas con pgvector

**Ejemplo conceptual**:
```
Cuenta: "5102 - Gastos de Publicidad"
Embedding: [0.1234, -0.5678, 0.9012, ...] (384 números)

Transacción: "Pago a Facebook Ads"  
Embedding: [0.1189, -0.5234, 0.8876, ...] (384 números)

Similitud matemática: 97.3% 
```

---

### 4. `transaccion_original`
**Propósito**: Almacena las transacciones tal como vienen del archivo Excel, sin procesar.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `fecha` | DATE | Fecha de la transacción |
| `descripcion` | TEXT | Descripción original del Excel |
| `monto` | DECIMAL(15,2) | Cantidad en dinero |
| `moneda` | VARCHAR(5) | USD, EUR, etc. |
| `archivo_origen` | VARCHAR(255) | Nombre del archivo Excel |
| `fila_origen` | INTEGER | Número de fila en el Excel |
| `procesada` | BOOLEAN | Si ya fue procesada por el LLM |
| `created_at` | TIMESTAMP | Cuando se cargó |

**Ejemplo**:
```
fecha: 2025-08-01
descripcion: "Venta de 5 camisetas"
monto: 50.00
moneda: USD
archivo_origen: "ventas_agosto.xlsx"
fila_origen: 2
```

---

### 5. `clasificacion_llm`
**Propósito**: Almacena las clasificaciones automáticas generadas por el **flujo RAG** (Retrieval-Augmented Generation).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `transaccion_original_id` | INTEGER | FK a `transaccion_original` |
| `tipo_transaccion` | VARCHAR(20) | INGRESO o EGRESO |
| `categoria_id` | INTEGER | FK a `categoria` **(para análisis gerencial)** |
| `cuenta_sugerida_id` | INTEGER | FK a `cuenta` **(para registro contable)** |
| `confianza` | DECIMAL(3,2) | Nivel de confianza del LLM (0.00-1.00) |
| `justificacion` | TEXT | **Explicación del LLM sobre su elección** |
| `revisada` | BOOLEAN | Si fue **validada por un humano** |
| `created_at` | TIMESTAMP | Cuándo se clasificó |


**Ejemplo del proceso**:
```
1. Transacción: "Pago de factura de internet de Tigo"

2. Búsqueda vectorial encuentra 5 candidatos:
   - 5201 - Servicios de Telecomunicaciones (similitud: 94.7%)
   - 5102 - Gastos de Oficina (similitud: 87.2%)
   - 5203 - Servicios Públicos (similitud: 82.1%)
   - 5105 - Gastos de Comunicación (similitud: 79.8%)
   - 5301 - Gastos Operativos (similitud: 72.3%)

3. LLM recibe solo estos 5 candidatos + la transacción

4. LLM responde: "5201 - Servicios de Telecomunicaciones"
   Justificación: "Es un gasto de internet de Tigo, claramente telecomunicaciones"
   Confianza: 0.96

5. Se guarda en clasificacion_llm ✅
```

- **Mayor precisión**: El LLM elige entre 5 opciones muy relevantes, no entre cientos
- **Menor costo**: Prompts más cortos = menos tokens = menos dinero
- **Mejor justificación**: El LLM puede explicar mejor su elección
- **Separación clara**: `categoria_id` para análisis, `cuenta_sugerida_id` para contabilidad

---

### 6. `asiento_contable`
**Propósito**: Los asientos contables formales (partida doble) que se generan del sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `numero_asiento` | VARCHAR(20) | Número único (ASI-2025-001) |
| `fecha` | DATE | Fecha del asiento |
| `descripcion` | TEXT | Descripción del asiento |
| `transaccion_original_id` | INTEGER | FK a `transaccion_original` |
| `total_debe` | DECIMAL(15,2) | Suma total del DEBE |
| `total_haber` | DECIMAL(15,2) | Suma total del HABER |
| `balanceado` | BOOLEAN | Si DEBE = HABER |
| `created_at` | TIMESTAMP | Fecha de creación |

---

### 7. `detalle_asiento`
**Propósito**: Los movimientos individuales de cada asiento contable (debe y haber).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `asiento_contable_id` | INTEGER | FK a `asiento_contable` |
| `cuenta_id` | INTEGER | FK a `cuenta` |
| `descripcion` | TEXT | Descripción del movimiento |
| `debe` | DECIMAL(15,2) | Cantidad en el DEBE |
| `haber` | DECIMAL(15,2) | Cantidad en el HABER |
| `orden` | INTEGER | Orden dentro del asiento |
| `created_at` | TIMESTAMP | Fecha de creación |

**Restricción importante**: Solo puede tener valor en DEBE o HABER, no ambos.

**Ejemplo de asiento balanceado**:
```
Asiento: ASI-2025-001 "Venta de productos"
├── Detalle 1: Caja (1101) - DEBE: $50.00
└── Detalle 2: Ventas (4101) - HABER: $50.00
Total DEBE: $50.00 = Total HABER: $50.00 ✅
```

---

### 8. `periodo_contable`
**Propósito**: Define períodos contables para filtrar reportes y análisis.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `nombre` | VARCHAR(50) | "Enero 2025", "Q1 2025", "2025" |
| `tipo_periodo` | VARCHAR(20) | MENSUAL, TRIMESTRAL, ANUAL |
| `fecha_inicio` | DATE | Inicio del período |
| `fecha_fin` | DATE | Fin del período |
| `año` | INTEGER | Año del período |
| `mes` | INTEGER | Mes (solo para MENSUAL) |
| `trimestre` | INTEGER | Trimestre (solo para TRIMESTRAL) |
| `activo` | BOOLEAN | Si está activo |
| `cerrado` | BOOLEAN | Si está cerrado contablemente |
| `created_at` | TIMESTAMP | Fecha de creación |

---

### 9. `auditoria`
**Propósito**: Registra TODOS los cambios realizados en el sistema para trazabilidad completa.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único automático |
| `tabla` | VARCHAR(50) | Nombre de la tabla modificada |
| `registro_id` | INTEGER | ID del registro modificado |
| `accion` | VARCHAR(20) | INSERT, UPDATE, DELETE |
| `valores_anteriores` | JSONB | Valores antes del cambio |
| `valores_nuevos` | JSONB | Valores después del cambio |
| `timestamp` | TIMESTAMP | Cuándo ocurrió |


---

## Secuencias

Las **secuencias** son contadores automáticos que PostgreSQL crea para campos `SERIAL`:

| Secuencia | Tabla | Propósito |
|-----------|-------|-----------|
| `tipo_cuenta_id_seq` | tipo_cuenta | Genera IDs únicos para tipos de cuenta |
| `cuenta_id_seq` | cuenta | Genera IDs únicos para cuentas |
| `transaccion_original_id_seq` | transaccion_original | Genera IDs únicos para transacciones |
| `clasificacion_llm_id_seq` | clasificacion_llm | Genera IDs únicos para clasificaciones |
| `asiento_contable_id_seq` | asiento_contable | Genera IDs únicos para asientos |
| `detalle_asiento_id_seq` | detalle_asiento | Genera IDs únicos para detalles |
| `periodo_contable_id_seq` | periodo_contable | Genera IDs únicos para períodos |
| `auditoria_id_seq` | auditoria | Genera IDs únicos para auditoría |

- Se incrementan automáticamente cada vez que insertas un registro
- Garantizan que los IDs sean únicos y consecutivos
- Son esenciales para el funcionamiento

---
## Vistas

Las **vistas** son "tablas virtuales" que muestran datos de varias tablas combinadas:

### `vista_libro_diario`
**Propósito**: Muestra todos los asientos contables como libro diario en formato cronológico.

**Campos mostrados**:
- `numero_asiento` - Número del asiento
- `fecha` - Fecha del asiento
- `descripcion` - Descripción del asiento
- `codigo_cuenta` - Código de la cuenta
- `nombre_cuenta` - Nombre de la cuenta
- `detalle_descripcion` - Descripción específica del movimiento
- `debe` - Monto en el debe
- `haber` - Monto en el haber

**Ordenamiento**: Por fecha, ID de asiento y orden de detalle

---

### `vista_libro_mayor`
**Propósito**: Muestra el libro mayor con saldos acumulados por cuenta, respetando la naturaleza contable.

**Campos mostrados**:
- `codigo_cuenta` - Código de la cuenta
- `nombre_cuenta` - Nombre de la cuenta
- `naturaleza` - DEUDORA o ACREEDORA
- `fecha` - Fecha del movimiento
- `numero_asiento` - Número del asiento
- `descripcion` - Descripción del movimiento
- `debe` - Monto en el debe
- `haber` - Monto en el haber
- `saldo` - Saldo acumulado calculado según naturaleza de cuenta

**Cálculo del saldo**:
- **Cuentas DEUDORAS**: `saldo = debe - haber` (acumulado)
- **Cuentas ACREEDORAS**: `saldo = haber - debe` (acumulado)

**Características de las vistas**:
- ✅ Simplifican consultas complejas
- ✅ Se actualizan automáticamente
- ✅ Perfectas para reportes
- ✅ No ocupan espacio adicional
- ✅ Incluyen ordenamiento lógico incorporado

---

## Funciones

Las **funciones** son código reutilizable que se ejecuta en la base de datos:

### `actualizar_totales_asiento()`
**Propósito**: Recalcula y actualiza automáticamente los totales `total_debe`, `total_haber` y el estado `balanceado` de un asiento contable cada vez que se inserta, modifica o elimina una de sus líneas de detalle.

**¿Qué hace?**
1. Identifica el asiento contable afectado por el cambio (funciona con INSERT, UPDATE y DELETE)
2. Suma todos los valores de la columna `debe` para ese asiento
3. Suma todos los valores de la columna `haber` para ese asiento
4. Actualiza los campos `total_debe`, `total_haber` y `balanceado` en la tabla `asiento_contable`
5. Determina si el asiento está balanceado (debe = haber)

**Características técnicas**:
- **Tipo de función**: TRIGGER
- **Retorno**: NULL (no necesita retornar valor)
- **Operaciones soportadas**: INSERT, UPDATE, DELETE
- **Usa**: COALESCE para manejar valores NULL correctamente

**Ejemplo**:
```sql
-- Cuando agregas un detalle:
INSERT INTO detalle_asiento (asiento_contable_id, cuenta_id, debe, orden) 
VALUES (1, 5, 100.00, 1);

-- La función automáticamente actualiza:
-- total_debe = suma de todos los debe del asiento
-- total_haber = suma de todos los haber del asiento
-- balanceado = true/false (total_debe = total_haber)
```

---

## Triggers (Disparadores)

Los **triggers** son "eventos automáticos" que se ejecutan cuando ocurre algo en la base de datos:

### Trigger de Totales de Asiento
**Se ejecuta**: DESPUÉS de cualquier cambio en `detalle_asiento`

| Trigger | Cuándo se ejecuta | Función ejecutada |
|---------|------------------|-------------------|
| `trg_detalle_totales_after_change` | Después de INSERT, UPDATE o DELETE | `actualizar_totales_asiento()` |


**¿Qué hace?**
- Recalcula automáticamente los totales del asiento padre
- Mantiene siempre actualizado el balance
- Garantiza integridad contable sin intervención manual
- Funciona para agregar, modificar o eliminar detalles

**Ejemplo práctico**:
```sql
-- 1. Tienes un asiento con total_debe = $100, total_haber = $100
-- 2. Agregas un nuevo detalle:
INSERT INTO detalle_asiento (asiento_contable_id, cuenta_id, debe, orden) 
VALUES (1, 3, 50.00, 2);

-- 3. El trigger automáticamente actualiza:
--    total_debe = $150
--    total_haber = $100  
--    balanceado = false (porque no están iguales)

-- 4. Agregas el contrapartida:
INSERT INTO detalle_asiento (asiento_contable_id, cuenta_id, haber, orden) 
VALUES (1, 4, 50.00, 3);

-- 5. El trigger actualiza nuevamente:
--    total_debe = $150
--    total_haber = $150
--    balanceado = true (ahora sí están iguales)
```

---
