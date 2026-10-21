<script setup>
// Marco de la aplicación (el mismo de facturacion): barra lateral, barra superior y contenido.
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Avisos from '@/componentes/Avisos.vue'
import Icono from '@/componentes/Icono.vue'
import { fijarTema, tema } from '@/nucleo/tema.js'

const route = useRoute()
const abierta = ref(false)
watch(() => route.fullPath, () => (abierta.value = false))

const PRODUCTOS = [
  { a: '/productos', nombre: 'Catálogo', icono: 'lista', seccion: 'catalogo' },
  { a: '/productos/nuevo', nombre: 'Nuevo producto', icono: 'mas', seccion: 'nuevo' },
  { a: '/productos/configuracion', nombre: 'Configuración', icono: 'engrane', seccion: 'configuracion' },
]
const TEMAS = [{ v: 'light', i: 'sol', n: 'Claro' }, { v: 'dark', i: 'luna', n: 'Oscuro' }, { v: 'sistema', i: 'monitor', n: 'Según el sistema' }]
const activo = (e) => route.meta.seccion === e.seccion
</script>

<template>
  <a class="saltar" href="#principal">Ir al contenido</a>
  <div class="marco">
    <aside class="lateral" :class="{ abierta }" aria-label="Navegación principal">
      <div class="lateral-cabeza">
        <RouterLink to="/" class="marca">
          <span class="marca-logo"><Icono nombre="caja" :tam="18" /></span>
          <span class="marca-texto">ERP<span>Gestión de productos</span></span>
        </RouterLink>
        <button type="button" class="btn-icono lateral-cerrar" aria-label="Cerrar menú" @click="abierta = false"><Icono nombre="cerrar" :tam="18" /></button>
      </div>
      <nav class="lateral-nav">
        <RouterLink to="/" class="lateral-item" :class="{ activo: route.name === 'inicio' }" :aria-current="route.name === 'inicio' ? 'page' : undefined">
          <Icono nombre="inicio" /><span class="lateral-texto">Inicio</span></RouterLink>
        <p class="lateral-grupo">Productos</p>
        <RouterLink v-for="e in PRODUCTOS" :key="e.a" :to="e.a" class="lateral-item" :class="{ activo: activo(e) }" :aria-current="activo(e) ? 'page' : undefined">
          <Icono :nombre="e.icono" /><span class="lateral-texto">{{ e.nombre }}</span></RouterLink>
      </nav>
      <div class="lateral-pie">
        <div class="tema" role="group" aria-label="Tema">
          <button v-for="x in TEMAS" :key="x.v" type="button" :aria-pressed="tema === x.v" :title="x.n" :aria-label="`Tema ${x.n.toLowerCase()}`" @click="fijarTema(x.v)">
            <Icono :nombre="x.i" :tam="16" /></button>
        </div>
      </div>
    </aside>
    <div v-if="abierta" class="lateral-velo" @click="abierta = false" />
    <div class="area">
      <header class="cabecera">
        <button type="button" class="btn btn-fantasma btn-cuadrado boton-menu" aria-label="Abrir menú" @click="abierta = true"><Icono nombre="menu" :tam="20" /></button>
        <span class="cabecera-titulo">{{ route.meta.titulo }}</span>
      </header>
      <main id="principal" class="contenido" tabindex="-1">
        <RouterView v-slot="{ Component }">
          <component :is="Component" />
        </RouterView>
      </main>
    </div>
  </div>
  <Avisos />
</template>

<style scoped>
.saltar { position: absolute; inset-inline-start: -9999px; top: 8px; z-index: 100; background: var(--acento); color: #fff; padding: 8px 12px; border-radius: 6px; }
.saltar:focus { inset-inline-start: 8px; }
.cabecera-titulo { font-weight: 620; color: var(--tinta-2); font-size: 0.92rem; }
main:focus { outline: none; }
</style>
