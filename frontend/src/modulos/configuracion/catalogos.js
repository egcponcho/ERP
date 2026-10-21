// Definición de las pantallas de catálogos simples: columnas de la tabla y campos del formulario.
// tipo de campo: texto | codigo | numero | bool | select (fuente = otro catálogo) | transiciones
export const CATALOGOS = {
  magnitudes: {
    singular: 'magnitud', nuevo: 'Nueva magnitud', titulo: 'Magnitudes', descripcion: 'Lo que se mide. Las unidades de una misma magnitud se convierten entre sí.',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'activa', tipo: 'bool' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
  unidades: {
    singular: 'unidad', nuevo: 'Nueva unidad', titulo: 'Unidades de medida', descripcion: 'El factor dice cuántas unidades de referencia de su magnitud contiene (kg = 1, g = 0.001).',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'simbolo', nombre: 'Símbolo' },
               { campo: 'magnitud_id', nombre: 'Magnitud', tipo: 'select', fuente: 'magnitudes' }, { campo: 'factor', tipo: 'numero' },
               { campo: 'decimales', tipo: 'numero' }, { campo: 'activa', tipo: 'bool' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'simbolo', nombre: 'Símbolo' }, { campo: 'magnitud_id', nombre: 'Magnitud', tipo: 'select', fuente: 'magnitudes', obligatorio: true },
             { campo: 'factor', nombre: 'Factor', tipo: 'numero', defecto: 1, ayuda: 'Unidades de referencia que contiene. Al cambiarlo se recalculan los valores capturados en esta unidad.' },
             { campo: 'decimales', nombre: 'Decimales', tipo: 'numero', defecto: 0, ayuda: '0 = se cuenta en enteros.' },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
  estados: {
    singular: 'estado', nuevo: 'Nuevo estado', titulo: 'Estados del producto', descripcion: 'El ciclo de vida. Si un estado no tiene pasos configurados, puede pasar a cualquier otro.',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'inicial', tipo: 'bool' },
               { campo: 'exige_completo', nombre: 'Exige ficha completa', tipo: 'bool' }, { campo: 'operable', tipo: 'bool' },
               { campo: 'transiciones', nombre: 'Puede pasar a', tipo: 'transiciones' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'orden', nombre: 'Orden', tipo: 'numero', defecto: 0 },
             { campo: 'inicial', nombre: 'Estado inicial de los productos nuevos', tipo: 'bool' },
             { campo: 'exige_completo', nombre: 'Exige ficha completa', tipo: 'bool', ayuda: 'Para entrar, el producto debe tener todos sus atributos obligatorios.' },
             { campo: 'operable', nombre: 'Operable', tipo: 'bool', ayuda: 'Compras, ventas e inventario pueden usar el producto.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true },
             { campo: 'transiciones', nombre: 'Puede pasar a', tipo: 'transiciones' }],
  },
  'grupos-atributo': {
    singular: 'grupo', nuevo: 'Nuevo grupo', titulo: 'Grupos de atributos', descripcion: 'Secciones en que se agrupan los atributos en la ficha.',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'orden', tipo: 'numero' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'orden', nombre: 'Orden', tipo: 'numero', defecto: 0 }, { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true }],
  },
  'tipos-identificador': {
    singular: 'tipo de identificador', nuevo: 'Nuevo tipo de identificador', titulo: 'Tipos de identificador', descripcion: 'Códigos alternos de los productos: EAN, UPC, código del proveedor, CAS…',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'patron', nombre: 'Formato', tipo: 'codigo' }, { campo: 'activo', tipo: 'bool' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'patron', nombre: 'Formato (expresión regular)', ayuda: 'Ejemplo: \\d{13} para 13 dígitos. Vacío = cualquier texto.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true }],
  },
  'tipos-relacion': {
    singular: 'tipo de relación', nuevo: 'Nuevo tipo de relación', titulo: 'Tipos de relación', descripcion: 'Vínculos entre productos: componentes, sustitutos, accesorios…',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'nombre_inverso', nombre: 'Nombre inverso' },
               { campo: 'con_cantidad', nombre: 'Con cantidad', tipo: 'bool' }, { campo: 'activo', tipo: 'bool' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'nombre_inverso', nombre: 'Nombre visto desde el otro producto', ayuda: 'Ejemplo: Componente → «Usado en».' },
             { campo: 'con_cantidad', nombre: 'Lleva cantidad', tipo: 'bool', ayuda: 'Para listas de materiales y kits.' },
             { campo: 'activo', nombre: 'Activo', tipo: 'bool', defecto: true }],
  },
  taxonomias: {
    singular: 'taxonomía', nuevo: 'Nueva taxonomía', titulo: 'Taxonomías', descripcion: 'Formas independientes de agrupar: línea comercial, familia contable, canal…',
    columnas: [{ campo: 'codigo', tipo: 'codigo' }, { campo: 'nombre' }, { campo: 'multiple', nombre: 'Varias categorías', tipo: 'bool' },
               { campo: 'obligatoria', tipo: 'bool' }, { campo: 'activa', tipo: 'bool' }],
    campos: [{ campo: 'codigo', nombre: 'Código', tipo: 'codigo', obligatorio: true }, { campo: 'nombre', nombre: 'Nombre', obligatorio: true },
             { campo: 'multiple', nombre: 'Un producto puede estar en varias categorías', tipo: 'bool' },
             { campo: 'obligatoria', nombre: 'Obligatoria para la ficha completa', tipo: 'bool' },
             { campo: 'activa', nombre: 'Activa', tipo: 'bool', defecto: true }],
  },
}

// Páginas: cada una muestra uno o más catálogos
export const PAGINAS = {
  unidades: { titulo: 'Unidades de medida', descripcion: 'Unidades en que se cuentan y miden los productos, agrupadas por magnitud.', catalogos: ['unidades', 'magnitudes'] },
  estados: { titulo: 'Estados', descripcion: 'El ciclo de vida de los productos y los pasos permitidos entre estados.', catalogos: ['estados'] },
  'tipos-identificador': { titulo: 'Identificadores', descripcion: 'Tipos de códigos alternos que se pueden asignar a productos, variantes y presentaciones.', catalogos: ['tipos-identificador'] },
  'tipos-relacion': { titulo: 'Relaciones', descripcion: 'Tipos de vínculo entre productos.', catalogos: ['tipos-relacion'] },
  'grupos-atributo': { titulo: 'Grupos de atributos', descripcion: 'Secciones de la ficha.', catalogos: ['grupos-atributo'] },
}
