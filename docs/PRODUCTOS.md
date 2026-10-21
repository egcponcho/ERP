# Módulo de productos

Un catálogo universal: el mismo modelo sirve para calzado, químicos, materias
primas, electrodomésticos, alimentos o cualquier otro rubro. Lo particular de
cada rubro se **configura**: no está escrito en el código ni en columnas de
la base de datos.

## Idea central

El producto solo guarda lo que tiene cualquier producto:

| Campo | Para qué |
|---|---|
| `codigo` | Único en la organización. Lo escribe la persona o lo genera la plantilla del tipo. |
| `nombre`, `descripcion` | Texto libre. |
| `tipo_id` | Tipo de producto: define qué atributos tiene. |
| `unidad_id` | Unidad base en que se cuenta o se mide. |
| `estado_id` | Estado del ciclo de vida, configurable. |

Todo lo demás (talla, color, número CAS, pureza, voltaje, vida útil, alérgenos,
peso, temporada…) es un **atributo** con su tipo de dato, sus reglas y,
cuando aplica, su unidad.

## Modelo

```
CONFIGURACIÓN (cada organización la administra)          DATOS

Magnitud ─< UnidadMedida                                  Producto ─< Variante (SKU)
GrupoAtributo ─< Atributo ─< AtributoOpcion               Producto/Variante ─< ValorAtributo ─< ValorAtributoOpcion
TipoProducto (árbol) ─< TipoProductoAtributo >─ Atributo  Producto ─< ProductoCategoria >─ Categoria
Taxonomia ─< Categoria (árbol)                            Producto ─< Presentacion
EstadoProducto ─< EstadoTransicion                        Producto ─< Identificador (de producto, variante o presentación)
TipoIdentificador                                         Producto ─< RelacionProducto >─ Producto
TipoRelacion                                              Producto ─< RevisionProducto
```

Todas las tablas llevan `organizacion_id`: una instalación puede servir a
varias empresas y cada una ve solo sus datos (`app/core/organizacion.py`).

### Atributos

Un atributo tiene un **tipo de dato**. Los tipos de dato son la única lista
fija del módulo, porque definen cómo se guarda y valida un valor y no son
reglas de negocio:

| Tipo de dato | Ejemplo | Reglas configurables |
|---|---|---|
| `texto` | Número CAS `77-92-9` | `longitud_min`, `longitud_max`, `patron` (expresión regular) |
| `entero` | Vida útil `180` | `minimo`, `maximo` |
| `decimal` | Pureza `99.5` | `minimo`, `maximo`, `decimales` |
| `entero`/`decimal` con magnitud | Peso `{"valor": 500, "unidad": "G"}` | las mismas, expresadas en la unidad por defecto |
| `booleano` | Peligroso `true` | — |
| `fecha` | Vence `2027-03-01` | `minimo`, `maximo` |
| `opcion` | Color `NEGRO` | sus opciones (tabla `atributo_opciones`) |
| `opciones` | Alérgenos `["GLUTEN", "LACTOSA"]` | `minimo`, `maximo` (cuántas elegir) |
| `referencia` | Producto base `15` | la entidad a la que apunta |

**Valores tipados, no JSON.** Cada valor es una fila de `valores_atributo`
con su columna según el tipo (`valor_texto`, `valor_numero`, `valor_fecha`,
`opcion_id`…), con llave foránea a su atributo, opción y unidad. Así se
puede filtrar e indexar, y la base protege la integridad: una opción en uso
no se puede borrar.

**Números con unidad.** Si el atributo tiene magnitud (masa, volumen…), el
valor se guarda tal como se capturó (500 g) y también en la unidad de
referencia (`valor_numero_base` = 0.5 kg). Los filtros y los rangos comparan
en la unidad de referencia, de modo que 500 g < 1 kg < 2 lb. Si se cambia el
factor de una unidad, se recalculan los valores capturados en ella.

**Referencias a otros maestros.** Un atributo `referencia` apunta a una
entidad registrada en `app/core/referencias.py`. Hoy está registrado
`producto`. Cuando se agreguen maestros (marcas, proveedores, fabricantes),
basta registrarlos para que cualquier tipo de producto los use como atributo,
sin tocar el modelo de productos. Un registro referenciado no se puede borrar
(`referencias.en_uso`).

### Tipos de producto

El tipo es la plantilla de un rubro. Asigna atributos (`tipo_producto_atributos`) indicando:

- `nivel`: `producto` (lo comparten todas las variantes) o `variante`.
- `es_eje`: el atributo distingue variantes (talla, color, voltaje). Solo en el nivel variante.
- `obligatorio`, `valor_defecto`, `orden`.
- `oculto`: quita un atributo heredado.

Los tipos forman un **árbol** (Electrodoméstico → Refrigerador → Minibar). Un
subtipo hereda los atributos, la unidad y las plantillas de sus antecesores,
y puede volver a asignar un atributo para cambiarlo u ocultarlo; la
asignación más cercana manda. `GET /api/productos/config/tipos-producto/{id}/esquema`
devuelve el resultado ya resuelto: es lo que la interfaz usa para armar el formulario.

Plantillas del tipo (heredables):

- `plantilla_codigo`: `CAL-{seq:05}` → CAL-00001, CAL-00002… El contador se bloquea al usarse.
- `plantilla_sku`: `{producto}-{color}-{talla}` → CAL-00001-NEGRO-38. Sin plantilla: código del producto + valores de los ejes.

### Variantes

Una variante es un SKU: el producto con un valor para cada eje. La
combinación de ejes se resume en una `firma` única por producto, así que no
puede haber dos variantes iguales (5 kg y 5000 g cuentan como iguales).
`POST /{id}/variantes/generar` crea todas las combinaciones de los valores
indicados y omite las que ya existen. Un tipo sin ejes no maneja variantes.

### Versiones

Hay dos conceptos distintos:

| Concepto | Qué es | Dónde |
|---|---|---|
| **Variante** | Versiones comerciales que existen a la vez (talla 38 y 39) | `variantes` |
| **Revisión** | Versiones de la ficha en el tiempo (receta 2026 y receta 2027) | `revisiones_producto` |

Publicar una revisión congela la ficha completa (datos, atributos,
categorías, variantes, presentaciones, identificadores y relaciones), cierra
la vigencia de la anterior y abre la nueva. Las revisiones no se modifican.
Además, cada producto y variante tiene un `version` de control de
concurrencia: si dos personas editan a la vez, la segunda recibe un 409.

### Clasificación

Las **taxonomías** son formas independientes de agrupar (Línea comercial,
Familia contable, Canal de venta…), cada una con su árbol de categorías.
Cada taxonomía indica si un producto puede estar en varias categorías
(`multiple`) y si es obligatoria para dar el producto por completo. El
filtro por categoría incluye sus subcategorías.

### Ciclo de vida

Los estados son configurables. `inicial` marca el estado de los productos
nuevos, `exige_completo` impide entrar a ese estado sin los atributos
obligatorios (también los de cada variante) y sin las taxonomías
obligatorias, y `operable` marca los estados en que otros módulos (compras,
ventas, inventario) pueden usar el producto. Las transiciones son opcionales:
si un estado no tiene transiciones configuradas, puede pasar a cualquier otro.

### Presentaciones, identificadores y relaciones

- **Presentación**: cómo se empaca o comercia (caja de 12, tambor de 250 kg),
  con su cantidad en la unidad base del producto. Puede ser de una variante.
- **Identificador**: códigos alternos (EAN-13, UPC, código del proveedor)
  con tipo configurable y patrón de validación. No se repiten dentro de su
  tipo. Se pueden asignar al producto, a una variante o a una presentación.
  `GET /api/productos/por-identificador?valor=...` encuentra el producto.
- **Relación**: vínculo dirigido entre productos con tipo configurable
  (Componente, Sustituto, Accesorio…). Si el tipo lleva cantidad, sirve como
  lista de materiales o kit. No se permiten ciclos dentro del mismo tipo, y
  un producto que es destino de una relación no se puede borrar.
  `GET /{id}/usado-en` muestra dónde se usa.

## Integridad

| Regla | Cómo se garantiza |
|---|---|
| Un valor pertenece a un producto o a una variante, nunca a ambos | `CHECK` en la base |
| Un atributo tiene un solo valor por producto o variante | `UNIQUE` en la base |
| No hay variantes repetidas | `UNIQUE (producto_id, firma)` |
| No se borra lo que está en uso | Llaves foráneas sin cascada y error 409. En ese caso se desactiva. |
| No se mezclan organizaciones | Filtro del ORM y revisión de cada llave foránea al guardar (`core/integridad.py`) |
| No se pierde un dato al cambiar la configuración | Con valores capturados no se puede cambiar el tipo de dato, la magnitud, el nivel ni los ejes. Un atributo oculto conserva sus valores en `atributos_fuera_de_esquema`. Cambiar de tipo de producto exige confirmar que se descartan los atributos que el nuevo tipo no tiene. |
| Ediciones simultáneas | `version` con bloqueo optimista |

## Cómo se modela cada rubro (ejemplos de las pruebas)

| Rubro | Atributos del producto | Ejes de variante | Otros |
|---|---|---|---|
| Calzado | material (opción, obligatorio), temporada | color, talla | Unidad PAR, código `CAL-{seq:05}`, SKU `{producto}-{color}-{talla}` |
| Químico | número CAS (texto con patrón), pureza (0–100 %, 2 decimales), peso neto (masa), contenido (volumen), peligroso | — | Presentación «Tambor 250 kg», EAN-13 en la presentación |
| Alimento | alérgenos (selección múltiple, máx. 2), vence (fecha), vida útil (entero) | — | Revisiones al cambiar la receta |
| Electrodoméstico | marca, garantía (con valor por defecto que el subtipo cambia) | voltaje | Árbol Electro → Refrigerador → Minibar |
| Mueble / kit | — | — | Lista de materiales con relaciones Componente |

`tests/` tiene cada uno de estos casos de punta a punta.

## API

Configuración (`/api/productos/config`): `magnitudes`, `unidades`,
`grupos-atributo`, `atributos` (con `/opciones`), `tipos-producto` (con
`/atributos` y `/esquema`), `taxonomias`, `categorias`, `estados` (con
`/transiciones`), `tipos-identificador`, `tipos-relacion` y
`entidades-referenciables`. Cada catálogo admite `GET` (lista y uno),
`POST`, `PATCH` y `DELETE`.

Productos (`/api/productos`):

| Ruta | Qué hace |
|---|---|
| `GET /` | Lista con filtros: `q`, `tipo_id` (incluye subtipos), `estado_id`, `categoria_id` (incluye subcategorías) y `a.<atributo>=valor`, `a.<atributo>__min`, `a.<atributo>__max` (por ejemplo `a.peso_neto__max=600 G`). Los filtros por atributo buscan en el producto y en sus variantes. |
| `POST /`, `GET/PATCH/DELETE /{id}` | Alta, ficha, edición (`version` obligatorio) y baja. |
| `POST /{id}/estado`, `GET /{id}/faltantes` | Cambio de estado y lo que falta para completar la ficha. |
| `POST /{id}/variantes`, `POST /{id}/variantes/generar`, `PATCH/DELETE /{id}/variantes/{v}` | Variantes. |
| `/{id}/presentaciones`, `/{id}/identificadores`, `/{id}/relaciones`, `GET /{id}/usado-en`, `GET /por-identificador` | Complementos. |
| `GET/POST /{id}/revisiones`, `GET /{id}/revisiones/{n}` | Revisiones. |

Los errores responden `{mensaje, codigo, detalle}` con 404 (no existe), 409
(conflicto o en uso) o 422 (validación, con la lista de campos en `detalle`).
La documentación interactiva está en `/docs`.

## Decisiones y límites conocidos

- **Por qué EAV tipado y no JSON.** Una columna JSON es más simple, pero no
  tiene llaves foráneas ni índices normales, y fue el origen de los valores
  huérfanos en `facturacion` (ver `AUDITORIA_PRODUCTOS.md`). El costo es que
  una ficha se arma con varias filas; las consultas cargan los valores con
  JOIN o `selectin`, así que no hay una consulta por atributo.
- **`referencia_id` no tiene llave foránea**, porque puede apuntar a
  cualquier entidad registrada. La existencia se valida al guardar y el
  borrado se protege con `referencias.en_uso`.
- **Cambiar el código de un producto no cambia los SKU** de sus variantes ya
  creados: un SKU publicado no debe cambiar solo.
- **Textos en un solo idioma.** Los nombres de atributos, opciones y tipos
  todavía no tienen traducción. Si hace falta, se agregará una tabla de
  traducciones por entidad sin cambiar este modelo.
- **Sin autenticación todavía.** La API trabaja en la organización
  `ORGANIZACION_POR_DEFECTO`. Al incorporar el módulo de acceso, la
  organización saldrá del usuario autenticado y solo cambia
  `app/web/dependencias.py`.

## Siguientes pasos sugeridos

1. Interfaz (Vue 3): configuración de atributos y tipos, y un formulario de
   producto armado desde `/esquema`.
2. Módulo de acceso (usuarios, roles, permisos por organización).
3. Los maestros que pida el siguiente módulo (por ejemplo marcas o
   proveedores), registrados como entidades referenciables.
4. Importación y exportación masiva (Excel) usando el mismo esquema.
