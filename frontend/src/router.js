import { createRouter, createWebHistory } from 'vue-router'
import { tituloPagina } from '@/nucleo/migas.js'

// Cada módulo es una sola entrada del menú; adentro tiene su tablero y sus apartados.
// meta.migas: ancestros para las migas de pan; meta.seccion: pestaña activa del módulo.
const PRODUCTOS = { texto: 'Productos', a: '/productos' }
const CATALOGO = { texto: 'Catálogo', a: '/productos/catalogo' }
const CONFIG = { texto: 'Configuración', a: '/productos/configuracion' }
const VISTAS = import.meta.glob('./modulos/productos/**/*.vue')
const vista = (ruta) => VISTAS[`./modulos/productos/${ruta}.vue`]
const config = (titulo, extra = {}) => ({ titulo, seccion: 'configuracion', migas: [PRODUCTOS, CONFIG], ...extra })

const routes = [
  { path: '/', name: 'inicio', component: () => import('@/modulos/inicio/InicioView.vue'), meta: { titulo: 'Inicio' } },
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
  // Direcciones anteriores
  { path: '/configuracion/:resto(.*)*', redirect: (to) => `/productos/configuracion/${[].concat(to.params.resto).join('/')}` },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Volver atrás devuelve a donde estaba; cambiar solo los filtros o la pestaña (query) no mueve la página
  scrollBehavior: (to, from, guardada) => guardada || (to.path === from.path ? false : { top: 0 }),
})
router.afterEach((to, from) => {
  if (to.path !== from.path) tituloPagina.value = ''
  document.title = `${to.meta.titulo || 'ERP'} · ERP`
})
export default router
