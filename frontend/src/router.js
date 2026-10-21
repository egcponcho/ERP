import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'inicio', component: () => import('@/modulos/inicio/InicioView.vue'), meta: { titulo: 'Inicio' } },
  { path: '/productos', name: 'productos', component: () => import('@/modulos/productos/ProductosView.vue'), meta: { titulo: 'Productos' } },
  { path: '/productos/:id(\\d+)', name: 'producto', component: () => import('@/modulos/productos/ProductoView.vue'), props: (r) => ({ id: Number(r.params.id) }), meta: { titulo: 'Producto' } },
  { path: '/configuracion/atributos', name: 'atributos', component: () => import('@/modulos/configuracion/AtributosView.vue'), meta: { titulo: 'Atributos' } },
  { path: '/configuracion/tipos', name: 'tipos', component: () => import('@/modulos/configuracion/TiposView.vue'), meta: { titulo: 'Tipos de producto' } },
  { path: '/configuracion/tipos/:id(\\d+)', name: 'tipo', component: () => import('@/modulos/configuracion/TipoView.vue'), props: (r) => ({ id: Number(r.params.id) }), meta: { titulo: 'Tipo de producto' } },
  { path: '/configuracion/categorias', name: 'categorias', component: () => import('@/modulos/configuracion/CategoriasView.vue'), meta: { titulo: 'Categorías' } },
  { path: '/configuracion/:catalogo', name: 'catalogo', component: () => import('@/modulos/configuracion/CatalogoView.vue'), props: true, meta: { titulo: 'Configuración' } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes, scrollBehavior: () => ({ top: 0 }) })
router.afterEach((to) => { document.title = `${to.meta.titulo || 'ERP'} · ERP` })
export default router
