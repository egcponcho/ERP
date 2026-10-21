import { createRouter, createWebHistory } from 'vue-router'

// Un solo módulo de productos: catálogo, asistente de alta, ficha y configuración
const routes = [
  { path: '/', name: 'inicio', component: () => import('@/modulos/inicio/InicioView.vue'), meta: { titulo: 'Inicio' } },
  {
    path: '/productos',
    component: () => import('@/modulos/productos/ModuloProductos.vue'),
    children: [
      { path: '', name: 'catalogo', component: () => import('@/modulos/productos/CatalogoView.vue'), meta: { titulo: 'Catálogo de productos', seccion: 'catalogo' } },
      { path: 'nuevo', name: 'nuevo', component: () => import('@/modulos/productos/asistente/AsistenteView.vue'), meta: { titulo: 'Nuevo producto', seccion: 'nuevo' } },
      { path: ':id(\\d+)', name: 'producto', component: () => import('@/modulos/productos/ficha/ProductoView.vue'),
        props: (r) => ({ id: Number(r.params.id) }), meta: { titulo: 'Producto', seccion: 'catalogo' } },
      {
        path: 'configuracion',
        component: () => import('@/modulos/productos/configuracion/ConfiguracionView.vue'),
        meta: { seccion: 'configuracion' },
        children: [
          { path: '', redirect: '/productos/configuracion/tipos' },
          { path: 'tipos', name: 'tipos', component: () => import('@/modulos/productos/configuracion/TiposSeccion.vue'), meta: { titulo: 'Tipos de producto', seccion: 'configuracion' } },
          { path: 'tipos/:id(\\d+)', name: 'tipo', component: () => import('@/modulos/productos/configuracion/TipoDetalle.vue'),
            props: (r) => ({ id: Number(r.params.id) }), meta: { titulo: 'Tipo de producto', seccion: 'configuracion', apartado: 'tipos' } },
          { path: 'atributos', name: 'atributos', component: () => import('@/modulos/productos/configuracion/AtributosSeccion.vue'), meta: { titulo: 'Características', seccion: 'configuracion' } },
          { path: 'categorias', name: 'categorias', component: () => import('@/modulos/productos/configuracion/CategoriasSeccion.vue'), meta: { titulo: 'Categorías', seccion: 'configuracion' } },
          { path: ':catalogo', name: 'catalogo-config', component: () => import('@/modulos/productos/configuracion/CatalogoSeccion.vue'), props: true, meta: { titulo: 'Configuración', seccion: 'configuracion' } },
        ],
      },
    ],
  },
  // Direcciones anteriores
  { path: '/configuracion/:resto(.*)*', redirect: (to) => `/productos/configuracion/${[].concat(to.params.resto).join('/')}` },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: () => ({ top: 0 }) })
router.afterEach((to) => { document.title = `${to.meta.titulo || 'ERP'} · ERP` })
export default router
