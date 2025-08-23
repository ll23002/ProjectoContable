Paso 1:
instalar requirements.txt

Paso 2:
Esquema de la BD


### 🔹 Descripción del esquema de la base de datos

#### `accounts`
Plan de cuentas contables.
- `code`: Código contable único
- `name`: Nombre de la cuenta
- `type`: Tipo de cuenta (`Activo`, `Pasivo`, `Patrimonio`, `Ingreso`, `Gasto`)
- `created_at`, `updated_at`: Timestamps

#### `categories`
Categorías para clasificación automática (LLM) de transacciones.
- `name`: Ej. `Ventas`, `Compras`, `Servicios`
- `description`: Opcional, explicación de la categoría

#### `periods`
Períodos contables para control de cierre.
- `start_date` / `end_date`: Rango del período
- `status`: `abierto` o `cerrado` (impide edición si está cerrado)
- `created_at`: Fecha de creación

#### `transactions`
Registro de cada transacción, ya sea ingresada manualmente o cargada desde Excel.
- `date`: Fecha de la transacción
- `description`: Descripción libre
- `amount`: Monto positivo
- `type`: `Ingreso` o `Egreso`
- `category_id`: Categoría asignada por LLM
- `account_id`: Cuenta contable asociada
- `period_id`: Período contable
- `lmm_confidence`: Confianza del modelo LLM (0.0 - 1.0)
- `created_at` / `updated_at`: Timestamps

#### `journals`
Asientos contables asociados a transacciones.
- `transaction_id`: FK a `transactions`
- `account_id`: Cuenta contable involucrada
- `debit` / `credit`: Montos del asiento
- `narration`: Descripción opcional de la línea
- `created_at` / `updated_at`: Timestamps

#### `transaction_logs`
Historial de cambios en transacciones (auditoría).
- `transaction_id`: FK a `transactions`
- `field_changed`: Campo modificado
- `old_value` / `new_value`: Valores antes y después del cambio
- `changed_at`: Fecha del cambio

---

### 🔹 Relaciones principales
- `transactions.category_id` → `categories.id`
- `transactions.account_id` → `accounts.id`
- `transactions.period_id` → `periods.id`
- `journals.transaction_id` → `transactions.id`
- `journals.account_id` → `accounts.id`
- `transaction_logs.transaction_id` → `transactions.id`



