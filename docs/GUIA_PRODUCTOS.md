# Guía del módulo de productos

Cómo funciona el módulo y cómo se usa, pantalla por pantalla. El diseño
técnico (tablas, reglas de integridad y API) está en [PRODUCTOS.md](PRODUCTOS.md).

## La idea en una frase

Un solo catálogo sirve para cualquier rubro (calzado, químicos, alimentos,
electrodomésticos, materias primas…). Lo que cambia de un rubro a otro no
está programado: se **configura** una vez y desde entonces el asistente de
alta pide exactamente lo que cada producto necesita.

## Las piezas, explicadas con un ejemplo

Supongamos una empresa que vende botas.

| Pieza | Qué es | En el ejemplo |
|---|---|---|
| **Tipo de producto** | La plantilla de un rubro: qué datos pide, cuáles distinguen variantes, en qué unidad se cuenta y cómo se numera. Los tipos forman un árbol y un subtipo hereda todo de su padre. | «Calzado», en pares, numerado `CAL-00001`, `CAL-00002`… |
| **Característica** | Un dato que se captura, con su tipo (texto, número, sí/no, fecha, una opción, varias opciones, referencia) y sus reglas. | Material (una opción: Cuero, Lona, Sintético), Color, Talla. |
| **Variante (SKU)** | Cada versión que se vende por separado. Sale de combinar las características que «distinguen variantes». | Color × Talla: `CAL-00001-NEGRO-38`, `CAL-00001-CAFE-39`… |
| **Presentación** | Cómo se empaca o se comercia, con su cantidad en la unidad base. | «Caja de 6 pares». |
| **Código** | Códigos alternos: de barras, del proveedor, CAS… Van en el producto, en una variante o en una presentación. | EAN-13 `7501234567890` en la caja de 6. |
| **Categoría** | Formas de agrupar. Cada forma (taxonomía) es un árbol propio: línea comercial, familia contable, canal de venta… | Canal de venta → Tienda. |
| **Estado** | El ciclo de vida. Unos estados exigen la ficha completa y otros dejan usar el producto en compras, ventas e inventario («operables»). | Borrador → Activo → Descontinuado. |
| **Revisión** | Una foto fija de la ficha completa en una fecha. Sirve para cambios formales (nueva receta, nuevo material) sin perder la historia. | Revisión 1 vigente desde hoy. |
| **Relación** | Un vínculo entre productos: componente, sustituto, accesorio. Con cantidad sirve como lista de materiales. | La bota lleva 1 «Plantilla dieléctrica». |

> **Variante o revisión.** Las variantes existen al mismo tiempo (talla 38 y
> talla 39). Las revisiones se suceden en el tiempo (la receta de 2026 y la
> de 2027). Son cosas distintas y el módulo maneja las dos.

## Dónde está cada cosa

En el menú lateral hay una sola entrada, **Productos**. Así el menú no se
satura cuando se agreguen más módulos (compras, ventas, inventario…). Todo
lo de productos vive adentro, en tres pestañas, y el botón **Nuevo producto**
está siempre a la vista:

```
Menú lateral            Productos
 Inicio                  ┌──────────────────────────────────────────────────┐
 MÓDULOS                 │ Resumen   Catálogo   Configuración  [+ Nuevo producto] │
 ▸ Productos             └──────────────────────────────────────────────────┘
```

- **Inicio** es el tablero general del ERP: una tarjeta por módulo con sus
  cifras clave y la actividad reciente.
- Arriba, las **migas de pan** dicen dónde está y permiten volver con un
  clic, por ejemplo: `Productos / Catálogo / Bota de trabajo dieléctrica`.
- Casi nada se abre en ventanas emergentes. Los formularios se abren en la
  misma página, las filas se editan al desplegarlas y para borrar, el mismo
  botón pregunta «¿Borrar? Sí / No».

## Resumen (el tablero del módulo)

Es lo primero que se ve al entrar a Productos.

1. **Puesta en marcha.** Aparece mientras falte algo indispensable y lista
   los pasos en orden: unidades y estados → tipos de producto con sus
   características → categorías (opcional) → primer producto. Cada paso
   lleva a donde se hace.
2. **Cifras.** Productos, operables, en borrador y variantes. Cada tarjeta
   abre el catálogo con ese filtro puesto.
3. **Productos por estado** y **por tipo.** Cada barra es un enlace al
   catálogo filtrado. El número siempre está escrito; la barra es solo de
   apoyo visual.
4. **Por completar.** Productos en borrador, sin códigos, sin presentaciones
   o sin categoría. Un clic abre exactamente esa lista para completarlos.
5. **Modificados recientemente.**

## Catálogo

La misma tabla de `facturacion`:

- **Buscar** por código, nombre o SKU de cualquier variante.
- **Ordenar y filtrar desde cada columna**, como en Excel: el embudo junto al
  título muestra los valores de la columna con cuántos productos tiene cada uno.
- **Categoría** y **Más filtros** para filtrar por cualquier característica
  (por ejemplo, Peso ≥ 2 kg, Color = Negro). Los números con unidad se
  comparan bien aunque estén en unidades distintas: 500 g < 1 kg < 2 lb.
- **Vistas guardadas**: guarde una combinación de filtros con un nombre.
- **Densidad** y **Columnas**: elija cuánta información ver y en qué orden.
- Los filtros activos se muestran como pastillas arriba de la tabla; la «x»
  de cada una lo quita.

Un clic en una fila abre la **ficha del producto**.

## Nuevo producto (el asistente paso a paso)

Un paso a la vez, con el avance arriba y un resumen al lado. Se puede volver
a cualquier paso sin perder nada. **El borrador se guarda solo** en el
navegador: si cierra o recarga, sigue donde iba. «Salir» no borra el
borrador; «Empezar de nuevo» sí.

1. **Tipo de producto.** Tarjetas con lo que pide cada tipo y si maneja
   variantes. Si el tipo no existe, **se crea ahí mismo**, incluso con
   características nuevas («Color: Negro, Blanco, Café»), y se marca cuáles
   distinguen variantes y cuáles son obligatorias.
2. **Datos generales.** Nombre, unidad y descripción. El código se genera
   solo con la plantilla del tipo (también se puede escribir).
3. **Características.** Solo las del tipo elegido, con las obligatorias
   marcadas con `*` y su avance. Las opciones se eligen con pastillas cuando
   son pocas y con una lista cuando son muchas.
4. **Variantes** (solo si el tipo tiene características que distinguen
   variantes). Se eligen los valores de cada una y la vista previa muestra
   todas las combinaciones; se desmarcan las que no existen. Lo que es igual
   para todas se captura una sola vez.
5. **Empaque y códigos.** Presentaciones (caja de 12, bulto de 50 kg…) y
   códigos de barras u otros, en líneas. Un código puede ir en una
   presentación.
6. **Categorías.**
7. **Revisar y crear.** Todo se valida en el servidor **sin guardar** y se
   muestran el código y los SKU reales que se van a crear. Se elige el estado
   final:
   - **Borrador**: se guarda aunque falten datos y se completa después.
   - **Activo** (u otro que exija ficha completa): solo si no falta nada.

   Si falta algo, la lista dice qué y lleva al paso donde se corrige. Al
   crear, todo se guarda junto o no se guarda nada.

## La ficha del producto

Arriba: código, estado (un clic en el estado muestra a cuáles puede pasar),
tipo, unidad, revisión y fecha. A la derecha, **Publicar revisión** y
**Borrar**. Si a la ficha le falta algo para un estado que exige ficha
completa, un aviso dice qué falta.

| Pestaña | Qué tiene |
|---|---|
| **Ficha** | Las características agrupadas por sección y las categorías. «Editar ficha» las vuelve campos en la misma página. Si el tipo dejó de pedir una característica, su valor se conserva y se puede descartar. |
| **Variantes** | Tabla con cada SKU. Al desplegar una fila se edita en la misma tabla. «Generar variantes» crea las combinaciones que falten. |
| **Presentaciones** | Nombre, cantidad y contenido se corrigen en la misma celda. |
| **Códigos** | Los códigos alternos y a qué se aplican (producto, variante o presentación). |
| **Relaciones** | Componentes, sustitutos, accesorios… y **Dónde se usa** (de qué otros productos es parte). |
| **Revisiones** | La historia de revisiones publicadas; al desplegar una se ve qué cambió respecto de la anterior. |

## Configuración

La portada agrupa los apartados por para qué sirven, en el orden en que
conviene configurarlos, y dice cuántos registros tiene cada uno (en naranja,
los que todavía no tienen ninguno). Dentro de un apartado, el menú de la
izquierda permite saltar a otro.

| Grupo | Apartado | Para qué |
|---|---|---|
| Estructura | **Tipos de producto** | Árbol de tipos. Cada tipo muestra sus características (propias y heredadas), cuáles distinguen variantes, cuáles son obligatorias, la vista previa de su ficha y «Ver productos». |
| | **Características** | Los datos que se pueden capturar, con su tipo de dato, reglas (mínimo, máximo, formato) y opciones. |
| | **Secciones de la ficha** | Agrupan las características en la ficha (Dimensiones, Seguridad…). |
| Clasificación | **Categorías** | Las taxonomías y el árbol de categorías de cada una. |
| Medidas | **Unidades** y **Magnitudes** | Las unidades (pieza, par, kg, litro…) y lo que miden. Las de una misma magnitud se convierten entre sí. |
| Ciclo de vida | **Estados** | Cuál es el inicial, cuáles exigen ficha completa, cuáles son operables y a cuáles se puede pasar desde cada uno. |
| Códigos y vínculos | **Tipos de código** y **Tipos de relación** | EAN, UPC, código del proveedor (con su formato), y componente, sustituto, accesorio. |

Cada catálogo simple muestra el formulario al lado de la tabla: un clic en
una fila la carga para editarla y «Nuevo» deja el formulario en blanco. Lo
que está en uso no se puede borrar; en ese caso se desactiva.

## Reglas que el sistema cuida solo

- No hay dos productos con el mismo código ni dos variantes con la misma combinación.
- Un código de barras no se repite dentro de su tipo.
- No se borra lo que está en uso (una opción usada, un producto que es componente de otro…).
- Si dos personas editan el mismo producto a la vez, la segunda recibe un aviso para recargar y no pisa los cambios.
- Cada empresa ve solo sus datos.

## Preguntas frecuentes

**¿Cómo agrego un rubro nuevo, por ejemplo químicos?** En el asistente,
paso 1, «Crear tipo nuevo». O en Configuración → Tipos de producto. No hace
falta programar nada.

**¿Puedo cambiar las características de un tipo con productos ya creados?**
Sí. Las nuevas aparecen vacías en los productos existentes y las que se
quitan conservan su valor en la ficha, que se puede descartar.

**¿Por qué no puedo activar un producto?** Porque el estado Activo exige la
ficha completa. El aviso de la ficha y el paso «Revisar y crear» dicen
exactamente qué falta.

**¿Dónde quedan las preferencias de las tablas?** En el navegador de cada
persona: columnas, densidad y vistas guardadas. Cuando exista el módulo de
usuarios pasarán a su perfil.
