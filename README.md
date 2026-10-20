# ERP

ERP modular y configurable. Se construye por etapas, tomando como base las
ideas del sistema `facturacion` (ver `docs/AUDITORIA_PRODUCTOS.md`) y
rediseñándolas para que nada propio de un rubro quede escrito en el código.

**Etapa actual: módulo de productos.** Es un catálogo universal (calzado,
químicos, materias primas, electrodomésticos, alimentos…) con atributos
dinámicos, tipos de producto heredables, variantes, revisiones, presentaciones,
identificadores, relaciones entre productos y estados configurables. El
diseño está en [docs/PRODUCTOS.md](docs/PRODUCTOS.md).

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic y PostgreSQL (SQLite para desarrollo y pruebas).
- **Varias organizaciones:** cada tabla lleva `organizacion_id` y el ORM aísla los datos de cada una.
- **Identificadores y textos en español.**

## Estructura

```
backend/
  app/
    core/          Núcleo transversal: base de datos, organización, errores, integridad, referencias
    web/           Dependencias compartidas de la API (sesión de la petición)
    modulos/
      productos/   modelos · esquemas · configuracion · esquema · valores · productos · complementos · api
    main.py
  alembic/         Migraciones
  tests/           Pruebas de punta a punta por rubro
docs/
  AUDITORIA_PRODUCTOS.md   Qué se tomó de facturacion y qué no
  PRODUCTOS.md             Diseño del módulo de productos
```

## Cómo empezar

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

alembic upgrade head                           # crea la base (SQLite: backend/erp.db)
python -m app.modulos.productos.instalacion    # opcional: unidades, estados y tipos sugeridos
uvicorn app.main:app --reload                  # API en http://localhost:8000, documentación en /docs
```

Con PostgreSQL: `DATABASE_URL=postgresql+psycopg://usuario:clave@host/base`.

## En la nube (Render)

El repositorio incluye `render.yaml`, que crea el servicio web desde el `Dockerfile`. **No crea la base de datos**, porque Render permite una sola base gratuita por cuenta. La base se indica en `DATABASE_URL`.

**1. Prepare la base.** Si ya tiene una instancia PostgreSQL en Render (por ejemplo, la de `facturacion`), cree dentro de ella una base aparte para el ERP. Así no se mezcla con las tablas de la otra aplicación:

1. En el panel de esa base, en **Connect**, copie el comando **PSQL Command** (o la **External Database URL**).
2. Ejecútelo en una terminal con `psql` instalado y escriba: `CREATE DATABASE erp;`
3. Tome la **Internal Database URL** de la instancia y cambie el nombre de la base del final por `erp`. Ejemplo: `postgresql://usuario:clave@dpg-xxxx-a/facturas` → `postgresql://usuario:clave@dpg-xxxx-a/erp`.

También sirve cualquier otra base PostgreSQL (una instancia pagada de Render, Neon, Supabase…).

**2. Cree el servicio.**

1. Entre a https://dashboard.render.com/blueprints y haga clic en **New Blueprint Instance**.
2. Conecte GitHub, elija este repositorio y la rama que quiere desplegar.
3. Render pide `DATABASE_URL`: pegue la dirección del paso 1.
4. Haga clic en **Apply**. En unos minutos queda en línea en `https://erp-XXXX.onrender.com`; la raíz abre la documentación interactiva de la API (`/docs`).

Al arrancar, el contenedor (`backend/arrancar.sh`) aplica las migraciones y, con `CARGAR_CONFIG_BASE=1`, agrega la configuración sugerida que falte. Si borra a propósito algo de esa configuración y no quiere que vuelva al reiniciar, cambie `CARGAR_CONFIG_BASE` a `0` en Render (*Environment*).

Límites del plan gratuito: el servicio se duerme tras 15 minutos sin uso (la primera petición tarda cerca de un minuto) y la base gratuita vence a los 30 días. Si la base del ERP está dentro de la instancia de otra aplicación, comparte con ella el vencimiento, el espacio (1 GB) y los respaldos.

## Pruebas

```bash
cd backend
pytest                                                                   # SQLite en memoria
TEST_DATABASE_URL=postgresql+psycopg://erp@localhost/erp_test pytest      # PostgreSQL (la base se vacía)
ruff check .
```
