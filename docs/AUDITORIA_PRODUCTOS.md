# Auditoría: productos y maestros relacionados en `facturacion`

Revisión de lo que hoy existe en `egcponcho/facturacion` (commit `3b9d8b5`) para
decidir qué ideas se llevan al módulo de productos del ERP y cuáles no.

Archivos revisados: `backend/app/modelos/productos.py`, `modelos/grupos.py`,
`modelos/maestros.py` (Articulo, Prepack, EscalaTalla, AtributoVariante,
ArticuloAtributo, UnidadMedida, CategoriaArticulo, GrupoArticulo, Marca,
ValorLista), `core/campos_propios.py`, `core/organizacion.py`,
`modulos/productos/*` y `modulos/productos/ficha.py`.

## Cómo está construido hoy

| Pieza | Qué es | Observación |
|---|---|---|
| `Producto` | Ficha de un **estilo-color de un proveedor** | La identidad del producto está atada a calzado y ropa: `estilo`, `color` y `proveedor_id` son columnas, y la clave única es `(proveedor_id, estilo, color)`. |
| `Articulo` | SKU = estilo + color + talla | `talla` y `color` son columnas fijas; `unidad` es un texto (`PAR \| UN \| CJ`) y `tipo` es `SOLIDO \| PREPACK`. |
| `AtributoVariante` + `ArticuloAtributo` | Ejes de variante propios de la empresa | Buena idea, pero los valores son siempre texto de 60 caracteres, sin tipo, sin opciones y sin validación; talla y color quedan como casos especiales (`columna IN ('talla','color')`). |
| `Producto.ficha` (JSON) + `ficha.py` | Atributos técnicos gobernados por datos (`AtributoDef`, `AtributoOpcion`, `AtributoAmbito`) | Es la parte más avanzada (ámbitos, derivaciones, bloqueos, implicaciones), pero está **acoplada al motor de clasificación arancelaria**: los ámbitos son capítulos, partidas y subpartidas del SAC y las secciones son una tupla en el código. Los valores viven en un JSON sin integridad referencial. |
| `campos_propios` | Campos extra por entidad en una columna `extra` JSON | Las entidades permitidas, los tipos y el máximo de 20 campos están en el código (`ENTIDADES`, `TIPOS`, `MAX_CAMPOS`). Al borrar una definición el valor queda huérfano en el JSON. |
| `GrupoProducto` | Árbol de familias y categorías | El árbol es buena idea, pero las clases están fijas (`FAMILIA`, `CATEGORIA`, con `CheckConstraint`) y solo existe un árbol por empresa. |
| `ProductoVersion` | Versiones cerradas de la ficha con vigencia | Buena idea (copia inmutable con vigencia `desde`/`hasta`), pero solo guarda la ficha y la clasificación arancelaria. |
| `Prepack` + `PrepackComponente` | Curvas y kits | La composición está bien modelada, pero solo admite `CURVA \| KIT` (`CheckConstraint`). |
| `UnidadMedida` | Catálogo de unidades | No tiene magnitud (masa, volumen…) ni factores de conversión; el artículo guarda el código de unidad como texto, no una llave foránea. |
| `EscalaTalla` | Escalas de tallas con regla de código | Útil solo para productos con talla. |

## Lo que se conserva (como idea, no como código)

1. **Aislamiento por organización** (`DeOrganizacion` + filtro del ORM + asignación al guardar). Se conserva la idea con una versión reducida.
2. **Atributos definidos por datos** (de `ficha.py`): definición, opciones, obligatoriedad y orden en tablas. Se conserva, ya sin depender de la clasificación arancelaria.
3. **Ejes de variante configurables** (`AtributoVariante`), extendidos a cualquier atributo con tipo.
4. **Versiones con vigencia** (`ProductoVersion`), extendidas a toda la ficha (datos generales, atributos y categorías).
5. **Árbol de grupos** (`GrupoProducto`), generalizado a varias taxonomías.
6. **Composición** (`PrepackComponente`), generalizada como relación entre productos con un tipo configurable.
7. **Control de concurrencia** (`version`), los errores de negocio con código (`ErrorNegocio`) y los identificadores en español.

## Lo que no se trae y por qué

| Problema en `facturacion` | Decisión en el ERP |
|---|---|
| Columnas propias de un rubro (`estilo`, `color`, `talla`, `proveedor_id`, `codigo` HS6, `sac_codigo`, `pais_origen`) | El producto solo tiene datos universales (código, nombre, tipo, unidad, estado). Todo lo demás son atributos configurados. |
| Listas fijas en el código (`SOLIDO/PREPACK`, `PAR/UN/CJ`, `FAMILIA/CATEGORIA`, `CURVA/KIT`, estados `borrador…corregido`, `SECCIONES`) | Cada una es una tabla configurable: tipos de producto, unidades, taxonomías, estados, tipos de relación y grupos de atributos. |
| Valores en JSON sin integridad (`ficha`, `extra`) | Los valores van en una tabla con columnas tipadas y llaves foráneas a su atributo, opción y unidad. |
| Unidad como texto | Llave foránea a `unidades_medida`, con su magnitud y su factor de conversión. |
| Lógica de clasificación arancelaria dentro de productos | Queda fuera. Cuando haga falta será un módulo aparte que lea los atributos del producto. |
| `campos_propios` con entidades fijas | Los atributos del producto cubren el caso. Si otros maestros necesitan campos propios, usarán el mismo motor de atributos. |
| Columnas «congeladas» de migraciones anteriores (`*_anterior_id`, `legado_*`) | No se traen: el ERP empieza con una sola migración inicial. |
| `productos.py` de 1,300 líneas que mezcla listado, ficha, aprobación, fotos y documentos | Servicios separados por responsabilidad: configuración, valores de atributos, productos, variantes y revisiones. |

## Riesgos detectados en el diseño original (para no repetirlos)

- **Integridad**: borrar una definición de campo propio deja valores huérfanos; en el ERP, una definición en uso solo se desactiva.
- **Unicidad de variantes**: nada impedía dos artículos con la misma combinación de ejes propios. En el ERP la combinación tiene una firma única por producto.
- **Búsqueda por atributo**: filtrar por un valor dentro de JSON necesita índices de expresión que se crean a mano (`_indice`). En el ERP los valores tipados tienen índices normales.
- **Hooks `before_flush` con lógica de negocio** (`_aplicar_variantes`): la lógica de negocio va en servicios explícitos y los hooks quedan solo para lo transversal (organización y fechas).
