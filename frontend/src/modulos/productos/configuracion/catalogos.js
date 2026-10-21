// Catálogos simples de la configuración: columnas de la tabla y campos del formulario.
// tipo de campo: texto | codigo | numero | bool | select (fuente = otro catálogo) | transiciones
const bool = (campo, texto, extra = {}) => ({ clave: campo, texto, valor: (f) => f[campo], textoValor: (v) => (v ? 'Sí' : 'No'), ...extra })

export const CATALOGOS = {
  unidades: {
    titulo: 'Unidades de medida', singular: 'unidad', nuevo: 'Nueva unidad',
    descripcion: 'En qué se cuentan y miden los productos. El factor dice cuántas unidades de referencia de su magnitud contiene (kg = 1, g = 0.001).',
    columnas: [{ clave: 'codigo', texto: 'Código', fija: true }, { clave: 'nombre', texto: 'Nombre' }, { clave: 'simbolo', texto: 'Símbolo', filtro: false },
               { clave: 'magnitud_id', texto: 'Magnitud', fuente: 'magnitudes' }, { clave: 'factor', texto: 'Factor', num: true, filtro: false },
               { clave: 'decimales', texto: 'Decimales', num: true }, bool('activa', 'Activa')],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'simbolo', nombre: 'Símbolo' }, { campo: 'magnitud_id', nombre: 'Magnitud', tipo: 'select', fuente: 'magnitudes', obligatorio: true },
             { campo: 'factor', nombre: 'Factor', tipo: 'numero', defecto: 1, ayuda: 'Al cambiarlo se recalculan los valores ya capturados en esta unidad.' },
             { campo: 'decimales', nombre: 'Decimales', tipo: 'numero', defecto: 0, ayuda: '0 = se cuenta en enteros.' },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
  magnitudes: {
    titulo: 'Magnitudes', singular: 'magnitud', nuevo: 'Nueva magnitud',
    descripcion: 'Lo que se mide (masa, volumen, longitud…). Las unidades de una misma magnitud se convierten entre sí.',
    columnas: [{ clave: 'codigo', texto: 'Código', fija: true }, { clave: 'nombre', texto: 'Nombre' }, bool('activa', 'Activa')],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
  estados: {
    titulo: 'Estados del producto', singular: 'estado', nuevo: 'Nuevo estado',
    descripcion: 'El ciclo de vida. Si un estado no tiene pasos configurados, puede pasar a cualquier otro.',
    columnas: [{ clave: 'orden', texto: '#', num: true, filtro: false }, { clave: 'nombre', texto: 'Nombre', fija: true }, bool('inicial', 'Inicial'),
               bool('exige_completo', 'Exige ficha completa'), bool('operable', 'Operable'), { clave: 'transiciones', texto: 'Puede pasar a', filtro: false, ordenable: false }],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'orden', nombre: 'Orden', tipo: 'numero', defecto: 0 },
             { campo: 'inicial', nombre: 'Estado de los productos nuevos', tipo: 'bool' },
             { campo: 'exige_completo', nombre: 'Exige ficha completa', tipo: 'bool', ayuda: 'Para entrar, el producto debe tener todos sus datos obligatorios.' },
             { campo: 'operable', nombre: 'Operable', tipo: 'bool', ayuda: 'Compras, ventas e inventario pueden usar el producto.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true },
             { campo: 'transiciones', nombre: 'Puede pasar a', tipo: 'transiciones' }],
  },
  'grupos-atributo': {
    titulo: 'Secciones de la ficha', singular: 'sección', nuevo: 'Nueva sección',
    descripcion: 'Agrupan las características en la ficha (Dimensiones, Seguridad, Datos técnicos…).',
    columnas: [{ clave: 'orden', texto: '#', num: true, filtro: false }, { clave: 'nombre', texto: 'Nombre', fija: true }, { clave: 'codigo', texto: 'Código' }],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'orden', nombre: 'Orden', tipo: 'numero', defecto: 0 }, { campo: 'activo', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
  'tipos-identificador': {
    titulo: 'Tipos de código', singular: 'tipo de código', nuevo: 'Nuevo tipo de código',
    descripcion: 'Códigos alternos de los productos: EAN, UPC, código del proveedor, CAS…',
    columnas: [{ clave: 'codigo', texto: 'Código', fija: true }, { clave: 'nombre', texto: 'Nombre' }, { clave: 'patron', texto: 'Formato', filtro: false }, bool('activo', 'Activo')],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'patron', nombre: 'Formato (expresión regular)', ayuda: 'Ejemplo: \\d{13} para 13 dígitos. Vacío = cualquier texto.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true }],
  },
  'tipos-relacion': {
    titulo: 'Tipos de relación', singular: 'tipo de relación', nuevo: 'Nuevo tipo de relación',
    descripcion: 'Vínculos entre productos: componentes, sustitutos, accesorios…',
    columnas: [{ clave: 'codigo', texto: 'Código', fija: true }, { clave: 'nombre', texto: 'Nombre' }, { clave: 'nombre_inverso', texto: 'Visto desde el otro' },
               bool('con_cantidad', 'Con cantidad'), bool('activo', 'Activo')],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'nombre_inverso', nombre: 'Nombre visto desde el otro producto', ayuda: 'Ejemplo: Componente → «Usado en».' },
             { campo: 'con_cantidad', nombre: 'Lleva cantidad', tipo: 'bool', ayuda: 'Para listas de materiales y kits.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true }],
  },
  taxonomias: {
    titulo: 'Taxonomías', singular: 'taxonomía', nuevo: 'Nueva taxonomía',
    descripcion: 'Formas independientes de agrupar: línea comercial, familia contable, canal de venta…',
    columnas: [{ clave: 'nombre', texto: 'Nombre', fija: true }, { clave: 'codigo', texto: 'Código' }, bool('multiple', 'Varias por producto'), bool('obligatoria', 'Obligatoria'), bool('activa', 'Activa')],
    campos: [{ campo: 'nombre', nombre: 'Nombre', obligatorio: true }, { campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true },
             { campo: 'multiple', nombre: 'Un producto puede estar en varias categorías', tipo: 'bool' },
             { campo: 'obligatoria', nombre: 'Obligatoria para la ficha completa', tipo: 'bool' },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
}

// Apartados de la configuración, agrupados por para qué sirven y en el orden en que conviene
// configurarlos. `fuente`: catálogo del que sale la cuenta de registros.
export const APARTADOS = [
  { grupo: 'Estructura de los productos', items: [
    { ruta: 'tipos', fuente: 'tipos-producto', nombre: 'Tipos de producto', icono: 'capas',
      texto: 'Qué datos pide cada clase de producto, cuáles distinguen variantes y cómo se numera.' },
    { ruta: 'atributos', fuente: 'atributos', nombre: 'Características', icono: 'etiqueta',
      texto: 'Los datos que se capturan (color, talla, peso, material…) con su tipo y sus reglas.' },
    { ruta: 'grupos-atributo', fuente: 'grupos-atributo', nombre: 'Secciones de la ficha', icono: 'lista',
      texto: 'Agrupan las características en la ficha: Dimensiones, Seguridad, Datos técnicos…' },
  ] },
  { grupo: 'Clasificación', items: [
    { ruta: 'categorias', fuente: 'categorias', nombre: 'Categorías', icono: 'arbol',
      texto: 'Árboles para agrupar productos: línea comercial, familia contable, canal de venta…' },
  ] },
  { grupo: 'Medidas', items: [
    { ruta: 'unidades', fuente: 'unidades', nombre: 'Unidades', icono: 'regla',
      texto: 'En qué se cuentan y miden los productos (pieza, par, kg, litro) y cómo se convierten.' },
    { ruta: 'magnitudes', fuente: 'magnitudes', nombre: 'Magnitudes', icono: 'escala',
      texto: 'Lo que se mide: masa, volumen, longitud… Agrupa las unidades convertibles entre sí.' },
  ] },
  { grupo: 'Ciclo de vida', items: [
    { ruta: 'estados', fuente: 'estados', nombre: 'Estados', icono: 'bandera',
      texto: 'Borrador, Activo, Descontinuado… cuáles exigen ficha completa y a cuáles se puede pasar.' },
  ] },
  { grupo: 'Códigos y vínculos', items: [
    { ruta: 'tipos-identificador', fuente: 'tipos-identificador', nombre: 'Tipos de código', icono: 'codigo',
      texto: 'Códigos alternos: EAN, UPC, código del proveedor, CAS…' },
    { ruta: 'tipos-relacion', fuente: 'tipos-relacion', nombre: 'Tipos de relación', icono: 'enlace',
      texto: 'Vínculos entre productos: componentes, sustitutos, accesorios…' },
  ] },
]
