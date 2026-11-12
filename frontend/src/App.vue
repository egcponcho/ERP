<script setup>
// Marco de la aplicación, armado con los contratos de los módulos (nucleo/modulos.js):
// - Escritorio y tableta: barra lateral (como la de iPadOS) con una entrada por módulo.
// - Celular: barra de pestañas abajo (como la de iOS) y botón «atrás» arriba.
// - Barra superior translúcida con la ubicación (migas) y el tema de colores.
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Avisos from '@/componentes/Avisos.vue'
import Icono from '@/componentes/Icono.vue'
import { tituloPagina } from '@/nucleo/migas.js'
import { cargarModulosActivos, modulosActivos } from '@/nucleo/modulos.js'
import { fijarTema, tema } from '@/nucleo/tema.js'

const route = useRoute()
const principal = ref(null)

onMounted(cargarModulosActivos)

// Al cambiar de página el foco pasa al contenido (lectores de pantalla)
watch(() => route.path, async (a, de) => {
  if (de === undefined) return
  await nextTick()
  principal.value?.focus({ preventScroll: true })
})

const destinos = computed(() => [
  { a: '/', nombre: 'Inicio', icono: 'inicio', activo: route.name === 'inicio' },
  ...modulosActivos.value.map((m) => ({ a: m.ruta, nombre: m.nombre, icono: m.icono, activo: route.meta.modulo === m.clave })),
])

const TEMAS = [{ v: 'light', i: 'sol', n: 'Claro' }, { v: 'dark', i: 'luna', n: 'Oscuro' }, { v: 'sistema', i: 'monitor', n: 'Automático' }]
const temaActual = computed(() => TEMAS.find((x) => x.v === tema.value) || TEMAS[2])
const siguienteTema = () => fijarTema(TEMAS[(TEMAS.indexOf(temaActual.value) + 1) % TEMAS.length].v)

const titulo = computed(() => tituloPagina.value || route.meta.titulo || '')
const migas = computed(() => [...(route.meta.migas || []), { texto: titulo.value }])
// En el celular, «atrás» lleva al nivel de arriba (la última miga con enlace)
const atras = computed(() => (route.meta.migas || []).at(-1) || null)
</script>

<template>
  <a class="saltar" href="#principal">Ir al contenido</a>
  <div class="marco">
    <aside class="lateral" aria-label="Menú principal">
      <RouterLink to="/" class="marca">
        <span class="marca-logo"><Icono nombre="cuadricula" :tam="17" /></span>
        <span class="marca-texto">ERP</span>
      </RouterLink>
      <nav class="lateral-nav" aria-label="Módulos">
        <RouterLink v-for="d in destinos" :key="d.a" :to="d.a" class="lateral-item" :class="{ activo: d.activo }"
                    :aria-current="d.activo ? 'page' : undefined">
          <Icono :nombre="d.icono" :tam="20" /><span class="lateral-texto">{{ d.nombre }}</span></RouterLink>
      </nav>
      <div class="lateral-pie">
        <div class="segmentos segmentos-chicos" role="group" aria-label="Apariencia">
          <button v-for="x in TEMAS" :key="x.v" type="button" class="segmento" :aria-pressed="tema === x.v" :title="x.n" :aria-label="`Apariencia: ${x.n.toLowerCase()}`" @click="fijarTema(x.v)">
            <Icono :nombre="x.i" :tam="15" /></button>
        </div>
      </div>
    </aside>

    <div class="area">
      <header class="cabecera">
        <RouterLink v-if="atras" :to="atras.a" class="cabecera-atras"><Icono nombre="atras-ios" :tam="22" /><span>{{ atras.texto }}</span></RouterLink>
        <nav class="migas" aria-label="Ubicación">
          <ol>
            <li v-for="(m, i) in migas" :key="i">
              <RouterLink v-if="m.a && i < migas.length - 1" :to="m.a">{{ m.texto }}</RouterLink>
              <span v-else aria-current="page">{{ m.texto }}</span>
            </li>
          </ol>
        </nav>
        <span class="cabecera-titulo" aria-hidden="true">{{ titulo }}</span>
        <button type="button" class="btn-icono cabecera-tema" :aria-label="`Apariencia: ${temaActual.n.toLowerCase()}. Cambiar`" @click="siguienteTema">
          <Icono :nombre="temaActual.i" :tam="20" /></button>
      </header>
      <main id="principal" ref="principal" class="contenido" tabindex="-1">
        <RouterView />
      </main>
    </div>

    <nav class="barra-pestanas" aria-label="Módulos">
      <RouterLink v-for="d in destinos" :key="d.a" :to="d.a" class="barra-pestana" :class="{ activo: d.activo }" :aria-current="d.activo ? 'page' : undefined">
        <Icono :nombre="d.icono" :tam="24" /><span>{{ d.nombre }}</span></RouterLink>
    </nav>
  </div>
  <Avisos />
</template>

<style scoped>
.saltar { position: absolute; inset-inline-start: -9999px; top: 8px; z-index: 100; background: var(--acento); color: var(--sobre-acento); padding: 8px 12px; border-radius: 10px; }
.saltar:focus { inset-inline-start: 8px; }
main:focus { outline: none; }
</style>
