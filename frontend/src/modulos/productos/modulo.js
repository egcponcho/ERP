// Contrato del módulo de productos en la interfaz (ver src/nucleo/modulos.js).
// Es lo único que el marco de la aplicación conoce del módulo: su entrada en el
// menú, su acción principal, sus rutas y su tarjeta en el Inicio general.
const PRODUCTOS = { texto: 'Productos', a: '/productos' }
const CATALOGO = { texto: 'Catálogo', a: '/productos/catalogo' }
const CONFIG = { texto: 'Configuración', a: '/productos/configuracion' }
const VISTAS = import.meta.glob('./**/*.vue')
const vista = (ruta) => VISTAS[`./${ruta}.vue`]
// meta.migas: ancestros para las migas de pan; meta.seccion: pestaña activa del módulo
const config = (titulo, extra = {}) => ({ titulo, seccion: 'configuracion', migas: [PRODUCTOS, CONFIG], ...extra })

export default {
  clave: 'productos',
  nombre: 'Productos',
  icono: 'caja',
  ruta: '/productos',
  accion: { texto: 'Nuevo producto', a: '/productos/nuevo', icono: 'mas' },
  // Apartados del módulo (control segmentado bajo el título)
  apartados: [
    { a: '/productos', nombre: 'Resumen', seccion: 'resumen' },
    { a: '/productos/catalogo', nombre: 'Catálogo', seccion: 'catalogo' },
    { a: '/productos/configuracion', nombre: 'Configuración', seccion: 'configuracion' },
  ],
  // Tarjeta del módulo en el Inicio general
  inicio: vista('inicio/TarjetaInicio'),
  rutas: [
    {
      path: '/productos',
      component: vista('ModuloProductos'),
      meta: { modulo: 'productos' },
      children: [
        { path: '', name: 'productos', component: vista('resumen/ResumenView'), meta: { titulo: 'Resumen', seccion: 'resumen', migas: [PRODUCTOS] } },
        { path: 'catalogo', name: 'catalogo', component: vista('catalogo/CatalogoView'), meta: { titulo: 'Catálogo', seccion: 'catalogo', migas: [PRODUCTOS] } },
        { path: 'nuevo', name: 'nuevo', component: vista('asistente/AsistenteView'), meta: { titulo: 'Nuevo producto', seccion: 'nuevo', migas: [PRODUCTOS] } },
        { path: ':id(\\d+)', name: 'producto', component: vista('ficha/ProductoView'), props: (r) => ({ id: Number(r.params.id) }),
          meta: { titulo: 'Producto', seccion: 'catalogo', migas: [PRODUCTOS, CATALOGO] } },
        {
          path: 'configuracion',
          component: vista('configuracion/ConfiguracionView'),
          children: [
            { path: '', name: 'configuracion', component: vista('configuracion/ConfiguracionInicio'), meta: { titulo: 'Configuración', seccion: 'configuracion', migas: [PRODUCTOS] } },
            { path: 'tipos', name: 'tipos', component: vista('configuracion/TiposSeccion'), meta: config('Tipos de producto') },
            { path: 'tipos/:id(\\d+)', name: 'tipo', component: vista('configuracion/TipoDetalle'), props: (r) => ({ id: Number(r.params.id) }),
              meta: config('Tipo de producto', { apartado: 'tipos', migas: [PRODUCTOS, CONFIG, { texto: 'Tipos de producto', a: '/productos/configuracion/tipos' }] }) },
            { path: 'atributos', name: 'atributos', component: vista('configuracion/AtributosSeccion'), meta: config('Características') },
            { path: 'categorias', name: 'categorias', component: vista('configuracion/CategoriasSeccion'), meta: config('Categorías') },
            { path: ':catalogo', name: 'catalogo-config', component: vista('configuracion/CatalogoSeccion'), props: true, meta: config('Configuración') },
          ],
        },
      ],
    },
  ],
}
