# Despliegue

El `Dockerfile` compila la interfaz (Vue) y la sirve desde el mismo contenedor que la API. Al arrancar, `backend/arrancar.sh` aplica las migraciones y, con `CARGAR_CONFIG_BASE=1`, ejecuta `python -m app.instalar` para cargar la configuración sugerida que falte de cada módulo activo. Con `MODULOS` se eligen los módulos.

## Railway

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

## Fly.io

El repositorio incluye `fly.toml`: Fly compila el `Dockerfile` (interfaz + API) y revisa `/api/salud`. La máquina se apaga sola cuando no hay tráfico y se enciende con la primera petición. La primera tarda unos segundos.

**1. Cree la aplicación** (una sola vez, en su computadora):

```bash
# Instalar flyctl: https://fly.io/docs/flyctl/install/
fly auth login
fly launch --copy-config --no-deploy    # usa este fly.toml; elija un nombre libre y la región
```

`fly launch` reescribe `app` y `primary_region` en `fly.toml` con lo que elija: súbalo al repositorio.

**2. La base de datos.** El ERP necesita PostgreSQL en `DATABASE_URL`:

- **Postgres administrado de Fly** (de pago, desde unos 38 USD al mes): créelo y conéctelo a la aplicación siguiendo https://fly.io/docs/mpg/ (con flyctl: `fly mpg create` y `fly mpg attach`). Al conectarlo, Fly guarda `DATABASE_URL` como secreto de la aplicación.
- **Otra base PostgreSQL** (Neon o Supabase tienen planes gratuitos, o la de Render o Railway): `fly secrets set DATABASE_URL="postgresql://usuario:clave@host/base?sslmode=require"`.

**3. Despliegue:** `fly deploy`. Queda en `https://<nombre>.fly.dev`. Al arrancar se aplican las migraciones y se carga la configuración sugerida que falte (`CARGAR_CONFIG_BASE` en `fly.toml`).

**Desde el panel de Fly** (*Launch an app from GitHub*), Fly despliega solo cada push a la rama elegida. Si se usa eso, no hace falta nada más. **Despliegue manual desde GitHub** (`.github/workflows/fly.yml`, *Actions → Desplegar en Fly.io → Run workflow*): no corre en cada push para no chocar con el del panel. Para usarlo, genere un token con `fly tokens create deploy -x 999999h` (copie todo, incluido `FlyV1 `) y guárdelo en GitHub → *Settings → Secrets and variables → Actions* con el nombre `FLY_API_TOKEN`. Sin ese secreto, el flujo no hace nada.

Si un despliegue falla con `failed to get lease on VM … lease currently held by …`, había otra operación sobre la misma máquina (otro despliegue o un cambio de secretos). Espere a la hora que indica `expires at` (un par de minutos) y vuelva a intentar.

## Render

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

