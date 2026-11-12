# Qué se toma de `facturacion` y qué no

El ERP nace de las ideas de `egcponcho/facturacion`, rediseñadas para que
nada propio de un rubro (calzado, ropa) ni de un país (aduanas
centroamericanas) quede escrito en el código. Este documento reemplaza a
`AUDITORIA_PRODUCTOS.md`, que se hizo sobre el commit `3b9d8b5` (19 oct 2026),
antes de la generalización G1–G6 de facturación. Está revisado contra el
commit `a295d81` (21 oct 2026). El análisis completo está en la carpeta del
proyecto (`analisis/AUDITORIA_FACTURACION.md`).

## Lo que se trae (como idea, no como código)

| Idea | En facturación | En el ERP |
|---|---|---|
| Multiempresa con aislamiento | `DeOrganizacion`, filtro del ORM, RLS | `core/organizacion.py` (filtro del ORM y revisión al guardar) |
| Atributos definidos por datos con tipo | `AtributoVariante` (G1–G6) y `AtributoDef` | Un solo motor: `valores_atributo` tipado, con unidad y opciones en tablas |
| Ejes de variante configurables | `AtributoVariante` | `es_eje` en la asignación al tipo; firma única por producto |
| Unidades con conversión | `maestros/unidades.py` | `Magnitud` + `UnidadMedida` con factor; los rangos comparan en la unidad base |
| Versiones del artículo | `ArticuloVersion` con huella | `RevisionProducto` con vigencia: congela la ficha completa |
| Árbol de grupos | `GrupoProducto` | Varias taxonomías independientes, cada una un árbol |
| Packs y kits | `Prepack` + `PrepackComponente` | Relaciones con tipo configurable y cantidad (lista de materiales) |
| Concurrencia, errores con código, dinero exacto | `version`, `ErrorNegocio`, `Decimal` | Igual |
| Tabla tipo Excel | `TablaDatos` | Igual, con el estilo del ERP |

## Lo que no se trae, y la regla que lo evita

| Problema en facturación | Regla en el ERP |
|---|---|
| Columnas de rubro: `estilo`, `color`, `talla` en artículo, línea de OC, línea de factura y prepack, sincronizadas con atributos por un hook | El producto solo tiene datos universales. Las líneas de documentos (cuando existan) guardan `variante_id` y la revisión; no copian atributos. |
| Cinco formas de agrupar (categoría, grupo, familia, dominio, `Producto.tipo`) | Tipos de producto para «qué datos pide» y taxonomías para «cómo se agrupa». Nada más. |
| Ficha técnica dentro del motor arancelario (SAC), atributos globales sin organización | Los atributos son de cada organización. La clasificación arancelaria, si llega, será un módulo enchufable que lee atributos por su código. |
| Producto con `proveedor_id` obligatorio | El producto no pertenece a un proveedor. Un futuro módulo de terceros se registra como entidad referenciable. |
| `productos` ↔ `clasificacion` en ciclo; `comun` y `acceso` dependen de módulos de negocio; 463 imports dentro de funciones | `tests/test_arquitectura.py`: core no conoce módulos, los módulos no se importan entre sí, sin imports en funciones. |
| Lógica de negocio en seis hooks `before_flush` cuyo orden importa | Solo hay hooks de organización y fechas. Variantes, versiones y validaciones se llaman desde el servicio. |
| Listas en `CheckConstraint` (tipos de almacén, estados, `CURVA/KIT`, `SOLIDO/PREPACK`) | Catálogos en tablas. Las únicas listas fijas son los tipos de dato del motor de atributos. |
| Datos de fábrica con rubro (CALZADO/ROPA, TALLA/COLOR, liberaciones 300/301/304) | `datos/base.json` es neutro. Los rubros se configuran o se cargan como plantillas opcionales. |
| Conocimiento de rubro en el código (parser de fibras, «talla × 10») | Plantillas de código y SKU como datos del tipo (`CAL-{seq:05}`, `{producto}-{color}-{talla}`). |
| Valores en JSON sin integridad (`ficha`, `extra`) | Columnas tipadas con llaves foráneas; un registro en uso no se borra, se desactiva. |
| Archivos de 1,300–1,600 líneas | Ninguno pasa de 500 (`tests/test_arquitectura.py`). |
| Columnas congeladas de migraciones (`*_anterior_id`, `legado_*`) | Una sola migración inicial; nada «que nada lee». |

## Orden sugerido para portar lo demás

Por dependencias: terceros y maestros → compras (OC) → facturación →
empaque → transporte y seguimiento. Clasificación arancelaria y etiquetado
pueden esperar porque son enchufables. En cada uno, antes de copiar una
columna, la pregunta es: ¿esto lo tiene cualquier empresa? Si no, es un
atributo o una configuración.
