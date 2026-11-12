# Arquitectura

El ERP es un **núcleo** pequeño más **módulos independientes**. Cada módulo
(productos hoy; terceros, compras, inventario mañana) vive en su carpeta, se
declara con un contrato y se puede apagar sin que nada más se rompa.

```
backend/app/
  core/                  Lo que comparte todo, sin saber de negocio
    config.py            Variables de entorno
    db.py                Motor y sesiones de SQLAlchemy
    modelo.py            Base de las tablas, tiempos y control de versión
    organizacion.py      Aislamiento por empresa (multiempresa)
    integridad.py        Llaves foráneas entre organizaciones y errores de la base
    errores.py           ErrorNegocio → {mensaje, codigo, detalle}
    sesion.py            Sesión de cada petición (aquí entrará el inicio de sesión)
    referencias.py       Registro de entidades a las que otros módulos pueden apuntar
    modulos.py           Contrato Modulo y registro de módulos
  modulos/
    productos/           Un módulo: modulo.py + modelos, servicios y rutas
  main.py                Arma la API con los módulos activos
  instalar.py            Carga los datos sugeridos de todos los módulos

frontend/src/
  nucleo/                Cliente de la API, avisos, tema, preferencias, registro de módulos
  componentes/           Piezas de interfaz comunes (tabla, asistente, marco del módulo…)
  estilos/               Tokens y hojas de estilo (design-system/ERP.md)
  inicio/                Inicio general: una tarjeta por módulo
  modulos/
    productos/           Un módulo: modulo.js + sus pantallas y compartido/
  App.vue                Marco: barra lateral, barra de pestañas, barra superior
  router.js              Inicio + las rutas que trae cada módulo
```

## Reglas de independencia

| Regla | Quién la revisa |
|---|---|
| `core` (backend) y `nucleo`/`componentes` (frontend) no importan ningún módulo | `tests/test_arquitectura.py`, `npm run lint` |
| Un módulo solo importa de `core` (o `nucleo`/`componentes`) y de sí mismo | las mismas |
| Sin imports dentro de funciones (esconden ciclos) | `tests/test_arquitectura.py` |
| Ningún archivo de más de 500 líneas | `tests/test_arquitectura.py` |
| Cada módulo tiene su contrato (`modulo.py` y `modulo.js`) | las mismas |
| La lógica de negocio va en servicios explícitos, no en eventos del ORM | revisión de código: los únicos eventos son los de `core/organizacion.py` |

### ¿Cómo se hablan dos módulos sin importarse?

Por **registros en `core`**: un módulo publica lo que ofrece y el otro lo usa
por su clave.

- `core.referencias`: el módulo de productos registra la entidad
  `"producto"`. Un atributo de tipo `referencia` (o un módulo futuro) guarda
  el id y pide la etiqueta con `referencias.etiquetas(db, "producto", ids)`.
  Antes de borrar un registro referenciable se pregunta
  `referencias.en_uso(...)` a todos los verificadores registrados.
- Si hace falta otro tipo de conexión (por ejemplo «antes de finalizar una
  factura, cada módulo valida lo suyo»), se agrega un registro igual en
  `core` y cada módulo se inscribe desde su `modulo.py`.

En la base de datos, una tabla de un módulo puede tener una llave foránea a
la tabla de otro solo si el contrato lo declara en `depende_de`; así el orden
de carga queda explícito y un módulo no arranca sin el que necesita.

## Cómo agregar un módulo

Ejemplo: un módulo `terceros` (clientes y proveedores).

**1. Backend.** `backend/app/modulos/terceros/`:

```python
# modulo.py
from app.core import referencias
from app.core.modulos import Modulo
from app.modulos.terceros import api
from app.modulos.terceros.instalacion import cargar_base
from app.modulos.terceros.modelos import Tercero


def _al_cargar() -> None:
    referencias.registrar("tercero", Tercero)   # un atributo de producto ya puede apuntar a un tercero


MODULO = Modulo(
    clave="terceros", nombre="Terceros", icono="usuario",
    descripcion="Clientes, proveedores y transportistas.",
    modelos="app.modulos.terceros.modelos",
    rutas=lambda: [api.router],
    instalar=cargar_base,
    al_cargar=_al_cargar,
)
```

Las tablas heredan `DeOrganizacion, ConTiempos, Base` (y `ConVersion` si se
editan a la vez) para quedar aisladas por empresa. Después:

```bash
cd backend
alembic revision --autogenerate -m "Terceros"   # revise el archivo generado
alembic upgrade head
pytest                                           # incluye las reglas de arquitectura
```

**2. Frontend.** `frontend/src/modulos/terceros/modulo.js` con `clave`,
`nombre`, `icono` (uno de `componentes/Icono.vue`), `ruta`, `apartados`,
`accion`, `inicio` (su tarjeta en el Inicio) y `rutas`. El menú, la barra de
pestañas del celular y el Inicio lo muestran solos. Use `MarcoModulo` para
el título, los apartados y la acción principal (ver `modulos/productos/`).

**3. Apagar un módulo.** `MODULOS=productos` en el servidor deja activos solo
los indicados. Sin la variable se cargan todos.

## Datos de partida neutros

Una organización nueva nace sin rubro: unidades del sistema internacional,
estados Borrador/Activo/Descontinuado, códigos EAN/UPC y relaciones
genéricas (`productos/datos/base.json`). Nada de tallas, colores, partidas
arancelarias ni categorías de una industria. Los rubros se configuran.
