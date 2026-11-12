// Rutas: el Inicio general más las que trae cada módulo en su contrato (modulo.js).
import { createRouter, createWebHistory } from 'vue-router'
import { tituloPagina } from '@/nucleo/migas.js'
import { MODULOS, estaActivo } from '@/nucleo/modulos.js'

const routes = [
  { path: '/', name: 'inicio', component: () => import('@/inicio/InicioView.vue'), meta: { titulo: 'Inicio' } },
  ...MODULOS.flatMap((m) => m.rutas),
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // Volver atrás devuelve a donde estaba; cambiar solo los filtros o la pestaña (query) no mueve la página
  scrollBehavior: (to, from, guardada) => guardada || (to.path === from.path ? false : { top: 0 }),
})

// Un módulo apagado en el servidor no se puede abrir por su dirección
router.beforeEach((to) => (to.meta.modulo && !estaActivo(to.meta.modulo) ? '/' : true))

router.afterEach((to, from) => {
  if (to.path !== from.path) tituloPagina.value = ''
  document.title = `${to.meta.titulo || 'Inicio'} · ERP`
})
export default router
