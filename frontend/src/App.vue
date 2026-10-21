<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Icono from '@/componentes/Icono.vue'
import Avisos from '@/componentes/Avisos.vue'
import { fijarTema, tema } from '@/nucleo/tema.js'

const route = useRoute()
const menuAbierto = ref(false)
watch(() => route.fullPath, () => (menuAbierto.value = false))

const SECCIONES = [
  { titulo: null, enlaces: [
    { a: '/', nombre: 'Inicio', icono: 'inicio', exacto: true },
    { a: '/productos', nombre: 'Productos', icono: 'caja' },
  ] },
  { titulo: 'Configuración', enlaces: [
    { a: '/configuracion/tipos', nombre: 'Tipos de producto', icono: 'capas' },
    { a: '/configuracion/atributos', nombre: 'Atributos', icono: 'etiqueta' },
    { a: '/configuracion/categorias', nombre: 'Categorías', icono: 'arbol' },
    { a: '/configuracion/unidades', nombre: 'Unidades', icono: 'regla' },
    { a: '/configuracion/estados', nombre: 'Estados', icono: 'bandera' },
    { a: '/configuracion/tipos-identificador', nombre: 'Identificadores', icono: 'codigo' },
    { a: '/configuracion/tipos-relacion', nombre: 'Relaciones', icono: 'enlace' },
  ] },
]
const TEMAS = [{ v: 'light', i: 'sol', n: 'Claro' }, { v: 'dark', i: 'luna', n: 'Oscuro' }, { v: 'sistema', i: 'monitor', n: 'Sistema' }]

function activo(e) {
  return e.exacto ? route.path === e.a : route.path.startsWith(e.a)
}
</script>

<template>
  <a class="saltar" href="#principal">Ir al contenido</a>
  <div class="marco">
    <aside class="lateral" :class="{ abierto: menuAbierto }" aria-label="Navegación principal">
      <div class="marca">
        <span class="logo" aria-hidden="true"><Icono nombre="caja" :tam="18" /></span>
        <span><strong>ERP</strong><small>Gestión de productos</small></span>
      </div>
      <nav>
        <div v-for="(s, i) in SECCIONES" :key="i" class="seccion">
          <p v-if="s.titulo" class="titulo-seccion">{{ s.titulo }}</p>
          <RouterLink v-for="e in s.enlaces" :key="e.a" :to="e.a" class="enlace" :class="{ activo: activo(e) }"
                      :aria-current="activo(e) ? 'page' : undefined">
            <Icono :nombre="e.icono" />{{ e.nombre }}
          </RouterLink>
        </div>
      </nav>
      <div class="temas" role="radiogroup" aria-label="Tema">
        <button v-for="t in TEMAS" :key="t.v" type="button" role="radio" :aria-checked="tema === t.v" :title="t.n"
                :aria-label="`Tema ${t.n.toLowerCase()}`" :class="{ activo: tema === t.v }" @click="fijarTema(t.v)">
          <Icono :nombre="t.i" :tam="16" />
        </button>
      </div>
    </aside>
    <div v-if="menuAbierto" class="velo-menu" @click="menuAbierto = false" />
    <div class="contenido">
      <header class="barra-movil">
        <button class="btn fantasma icono" type="button" aria-label="Abrir menú" @click="menuAbierto = true"><Icono nombre="menu" /></button>
        <strong>ERP</strong>
      </header>
      <main id="principal" tabindex="-1">
        <RouterView v-slot="{ Component }">
          <Transition name="vista" mode="out-in"><component :is="Component" :key="route.path" /></Transition>
        </RouterView>
      </main>
    </div>
  </div>
  <Avisos />
</template>

<style scoped>
.saltar { position: absolute; left: -9999px; top: 8px; z-index: 100; background: var(--acento); color: #fff; padding: 8px 12px; border-radius: 6px; }
.saltar:focus { left: 8px; }
.marco { display: flex; min-height: 100vh; }
.lateral { width: 248px; flex: none; background: var(--lateral); color: var(--lateral-texto); display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; padding: var(--e-4) var(--e-3); gap: var(--e-4); }
.marca { display: flex; align-items: center; gap: var(--e-3); padding: var(--e-1) var(--e-2) var(--e-3); border-bottom: 1px solid var(--lateral-linea); }
.marca strong { color: #fff; display: block; font-size: 15px; }
.marca small { color: var(--lateral-tenue); font-size: 12px; }
.logo { width: 34px; height: 34px; border-radius: 9px; background: linear-gradient(135deg, #4a6cf7, #2d47c9); color: #fff; display: grid; place-items: center; box-shadow: 0 4px 12px rgba(51, 85, 224, 0.4); }
nav { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: var(--e-4); }
.titulo-seccion { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--lateral-tenue); padding: 0 var(--e-3); margin-bottom: var(--e-1); font-weight: 600; }
.seccion { display: flex; flex-direction: column; gap: 2px; }
.enlace { display: flex; align-items: center; gap: var(--e-3); padding: 8px var(--e-3); border-radius: var(--radio); color: var(--lateral-texto); font-weight: 500; transition: background-color 0.15s, color 0.15s; }
.enlace:hover { background: rgba(255, 255, 255, 0.06); color: #fff; text-decoration: none; }
.enlace.activo { background: var(--lateral-activo-fondo); color: #fff; box-shadow: inset 2px 0 0 var(--lateral-acento); }
.enlace.activo :deep(svg) { color: var(--lateral-acento); }
.enlace:focus-visible { outline-color: var(--lateral-acento); }
.temas { display: flex; gap: 2px; padding: 3px; border-radius: var(--radio); background: rgba(255, 255, 255, 0.05); align-self: flex-start; }
.temas button { width: 32px; height: 28px; border: 0; border-radius: 6px; background: transparent; color: var(--lateral-tenue); cursor: pointer; display: grid; place-items: center; }
.temas button:hover { color: #fff; }
.temas button.activo { background: rgba(255, 255, 255, 0.12); color: #fff; }
.contenido { flex: 1; min-width: 0; }
main:focus { outline: none; }
.barra-movil { display: none; }
.vista-enter-active, .vista-leave-active { transition: opacity 0.12s ease; }
.vista-enter-from, .vista-leave-to { opacity: 0; }
@media (max-width: 900px) {
  .lateral { position: fixed; z-index: 40; left: 0; transform: translateX(-100%); transition: transform 0.2s ease; }
  .lateral.abierto { transform: none; }
  .velo-menu { position: fixed; inset: 0; background: var(--velo); z-index: 30; }
  .barra-movil { display: flex; align-items: center; gap: var(--e-2); padding: var(--e-2) var(--e-3); border-bottom: 1px solid var(--linea); background: var(--superficie); position: sticky; top: 0; z-index: 10; }
}
</style>
