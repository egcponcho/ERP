# ERP

ERP modular, genérico y multiempresa. Lo particular de cada empresa o rubro
(qué datos tiene un producto, cómo se numera, cómo se agrupa, su ciclo de
vida) se **configura**; no está escrito en el código.

Hoy trae el módulo de **Productos**: un catálogo universal con tipos de
producto heredables, características con tipo de dato, variantes (SKU),
presentaciones, códigos, relaciones, revisiones y estados configurables.
Sirve igual para calzado, químicos, alimentos o electrodomésticos.

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL (SQLite en desarrollo y pruebas).
- **Frontend:** Vue 3 + Vite, sin librerías de componentes. Estilo de iOS, tema claro y oscuro, accesible.
- **Módulos independientes:** cada uno se declara con un contrato y se puede apagar. Ver [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

## Cómo empezar

Necesita Python 3.12+ y Node.js 20+.

```bash
# Terminal 1: la API en http://localhost:8000
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head                                  # crea la base (SQLite: backend/erp.db)
python -m app.instalar                                # configuración sugerida de cada módulo
uvicorn app.main:app --reload

# Terminal 2: la interfaz en http://localhost:5173
cd frontend
npm install
npm run dev
```

Abra **http://localhost:5173**. La documentación de la API está en
http://localhost:8000/docs. Para un solo servidor: `npm run build` en
`frontend` y la API sirve la interfaz en http://localhost:8000.

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | Base de datos, por ejemplo `postgresql://usuario:clave@host/base` |
| `MODULOS` | Módulos activos, separados por coma. Sin ella, todos. |
| `ORGANIZACION_POR_DEFECTO` | Empresa con la que trabaja la API mientras no haya inicio de sesión (1) |

## Estructura

```
backend/
  app/core/            Núcleo sin negocio: base de datos, multiempresa, errores, registro de módulos
  app/modulos/<clave>/ Un módulo: modulo.py (contrato), modelos, servicios, api
  app/main.py          Arma la API con los módulos activos
  app/instalar.py      Datos sugeridos de todos los módulos
  alembic/             Migraciones
  tests/               Pruebas por rubro y reglas de arquitectura
frontend/src/
  nucleo/              API, avisos, tema, preferencias, registro de módulos
  componentes/         Piezas comunes (TablaDatos, Asistente, MarcoModulo…)
  estilos/             Tokens y hojas de estilo
  inicio/              Inicio general
  modulos/<clave>/     Un módulo: modulo.js (contrato) y sus pantallas
design-system/ERP.md   Guía visual
docs/
  ARQUITECTURA.md      Cómo está armado y cómo agregar un módulo
  PRODUCTOS.md         Diseño del módulo de productos (modelo, reglas, API)
  GUIA_PRODUCTOS.md    Cómo se usa, pantalla por pantalla
  DESDE_FACTURACION.md Qué se tomó del sistema anterior y qué reglas evitan repetir sus problemas
  DESPLIEGUE.md        Railway, Fly.io y Render
```

## Pruebas

```bash
cd backend
pytest                                                                   # SQLite en memoria
TEST_DATABASE_URL=postgresql+psycopg://erp@localhost/erp_test pytest      # PostgreSQL (la base se vacía)
ruff check .

cd ../frontend
npm run lint      # ESLint + independencia de módulos
npm run build
```

`tests/test_arquitectura.py` y `npm run lint` fallan si un módulo importa a
otro, si `core` conoce un módulo o si un archivo pasa de 500 líneas.

## En la nube

El `Dockerfile` compila la interfaz y la sirve junto a la API. Al arrancar
aplica las migraciones y, con `CARGAR_CONFIG_BASE=1`, carga la configuración
sugerida que falte. Pasos para Railway, Fly.io y Render en
[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).
