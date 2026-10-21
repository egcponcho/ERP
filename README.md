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
- **Frontend:** Vue 3 + Vite, sin librerías de componentes; tema claro y oscuro, accesible con teclado y lector de pantalla.
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

Necesita Python 3.12+ y Node.js 20+.

```bash
# Terminal 1: la API en http://localhost:8000
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head                                  # crea la base (SQLite: backend/erp.db)
python -m app.modulos.productos.instalacion           # opcional: unidades, estados y tipos sugeridos
uvicorn app.main:app --reload

# Terminal 2: la interfaz en http://localhost:5173 (redirige /api al puerto 8000)
cd frontend
npm install
npm run dev
```

Abra **http://localhost:5173**. La documentación de la API sigue en http://localhost:8000/docs.

Para usar un solo servidor: `npm run build` dentro de `frontend` y la API sirve la interfaz compilada en http://localhost:8000.

Con PostgreSQL: `DATABASE_URL=postgresql+psycopg://usuario:clave@host/base`.

### Interfaz

Vue 3 + Vite, sin librerías de componentes. Usa el **mismo sistema visual y las mismas piezas que `facturacion`**: estilos, marco, tabla común (`TablaDatos`: orden y filtro por columna como en Excel, columnas, densidad, vistas guardadas, detalle desplegable, paginación) y asistente por pasos. Casi no hay ventanas emergentes: los formularios se abren dentro de la página (`PanelEnLinea`), las filas se editan al desplegarlas y las bajas se confirman en el mismo botón (`BotonConfirmar`).

Todo vive en un solo módulo, **Productos**, con tres apartados:

- **Catálogo** (`modulos/productos/CatalogoView.vue`): la tabla común en modo servidor, con búsqueda, categoría y filtros por cualquier característica. Cada producto abre su ficha (`ficha/`) con pestañas: ficha, variantes, presentaciones, códigos, relaciones y revisiones.
- **Nuevo producto** (`modulos/productos/asistente/`): asistente paso a paso con el tipo de producto (que se puede crear ahí mismo, con características nuevas), los datos generales, las características, las variantes (combinaciones con vista previa), el empaque y los códigos, las categorías y una revisión final. La revisión valida todo en el servidor sin guardar y muestra los códigos y SKU reales. El borrador se guarda solo en el navegador y el alta completa se guarda en una sola transacción (`POST /api/productos/asistente`).
- **Configuración** (`modulos/productos/configuracion/`): menú lateral de apartados. Tiene tipos de producto (con herencia y vista previa de la ficha), características, secciones, categorías, unidades, magnitudes, estados, tipos de código y de relación. Cada catálogo muestra el formulario al lado de la tabla.

`componentes/CampoAtributo.vue` dibuja el control de cualquier característica según su tipo de dato: ninguna pantalla conoce los atributos de un rubro.

## En la nube (Railway)

El repositorio incluye `railway.json`: Railway compila el `Dockerfile` (interfaz + API) y revisa `/api/salud` antes de dar por bueno cada despliegue.

1. En https://railway.com/new elija **Deploy from GitHub repo** y seleccione este repositorio.
2. En el servicio creado, **Settings → Source**, elija la rama que quiere desplegar.
3. En el proyecto, **+ Create → Database → PostgreSQL**.
4. En el servicio de la app, **Variables**, agregue:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` (referencia a la base del paso 3)
   - `CARGAR_CONFIG_BASE` = `1`
   - `FORWARDED_ALLOW_IPS` = `*`
5. **Settings → Networking → Generate Domain**: Railway le da una dirección pública `https://….up.railway.app`.

Cada push a la rama elegida se despliega solo. Al arrancar se aplican las migraciones y se carga la configuración sugerida que falte.

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
4. Haga clic en **Apply**. En unos minutos queda en línea en `https://erp-XXXX.onrender.com`; la raíz abre la interfaz y la API queda en `/api` (documentación en `/docs`).

Al arrancar, el contenedor (`backend/arrancar.sh`) aplica las migraciones y, con `CARGAR_CONFIG_BASE=1`, agrega la configuración sugerida que falte. Si borra a propósito algo de esa configuración y no quiere que vuelva al reiniciar, cambie `CARGAR_CONFIG_BASE` a `0` en Render (*Environment*).

Límites del plan gratuito: el servicio se duerme tras 15 minutos sin uso (la primera petición tarda cerca de un minuto) y la base gratuita vence a los 30 días. Si la base del ERP está dentro de la instancia de otra aplicación, comparte con ella el vencimiento, el espacio (1 GB) y los respaldos.

## Pruebas

```bash
cd backend
pytest                                                                   # SQLite en memoria
TEST_DATABASE_URL=postgresql+psycopg://erp@localhost/erp_test pytest      # PostgreSQL (la base se vacía)
ruff check .

cd ../frontend && npm run lint && npm run build
```
