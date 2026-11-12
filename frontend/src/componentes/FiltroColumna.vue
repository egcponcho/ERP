<script setup>
import { t } from '@/nucleo/texto.js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { abrirCapa, cerrarCapa, esLaDeArriba } from '@/nucleo/capas.js'
import Icono from './Icono.vue'

// Filtro de una columna, como el de Excel: busca entre los valores que tiene
// la columna, se marcan uno o varios y se aplica. Flota sobre la página (no lo
// recorta el marco de la tabla) junto al encabezado que lo abrió.
//   ancla: el botón del encabezado; titulo: nombre de la columna
//   cargar(q): promesa o lista de { valor, texto, n } (n = filas con ese valor)
//   elegidos: valores marcados ahora (texto)
// Eventos: aplicar (lista de valores, o null para quitar el filtro), cerrar.
const props = defineProps({
  ancla: { type: Object, default: null },
  titulo: { type: String, default: '' },
  cargar: { type: Function, required: true },
  elegidos: { type: Array, default: () => [] },
})
const emit = defineEmits(['aplicar', 'cerrar'])

const VACIO = '__vacio__'
const q = ref('')
const opciones = ref([])
const cargando = ref(false)
const truncado = ref(false)
const marcados = ref(new Set(props.elegidos.map(String)))
// Lo que se conoce de cada valor elegido aunque la búsqueda ya no lo muestre
const conocidos = ref(new Map())
const raiz = ref(null)
const buscador = ref(null)
const pos = ref({ top: 0, left: 0 })
const MAXIMO = 200

let turno = 0
async function pedir() {
  const n = ++turno
  cargando.value = true
  try {
    const r = await props.cargar(q.value.trim())
    if (n !== turno) return
    const lista = (r || []).map((x) => ({ valor: x.valor === null || x.valor === undefined || x.valor === '' ? VACIO : String(x.valor),
      texto: x.valor === null || x.valor === undefined || x.valor === '' ? t('(Vacío)') : String(x.texto ?? x.valor), n: x.n }))
    truncado.value = lista.length > MAXIMO
    opciones.value = lista.slice(0, MAXIMO)
    for (const o of opciones.value) conocidos.value.set(o.valor, o.texto)
  } finally {
    if (n === turno) cargando.value = false
  }
}
let espera
function buscar() {
  clearTimeout(espera)
  espera = setTimeout(pedir, 200)
}

const todos = computed(() => opciones.value.length > 0 && opciones.value.every((o) => marcados.value.has(o.valor)))
function alternarTodos() {
  const s = new Set(marcados.value)
  if (todos.value) opciones.value.forEach((o) => s.delete(o.valor))
  else opciones.value.forEach((o) => s.add(o.valor))
  marcados.value = s
}
function alternar(v) {
  const s = new Set(marcados.value)
  if (s.has(v)) s.delete(v)
  else s.add(v)
  marcados.value = s
}
function aplicar() {
  emit('aplicar', marcados.value.size ? [...marcados.value] : null)
}
function limpiar() {
  emit('aplicar', null)
}

// Posición: debajo del encabezado; si no cabe abajo, encima; nunca fuera de la pantalla
function ubicar() {
  const r = props.ancla?.getBoundingClientRect()
  if (!r) return
  const ancho = Math.min(300, window.innerWidth - 16)
  const alto = raiz.value?.offsetHeight || 0
  let top = r.bottom + 6
  if (alto && top + alto > window.innerHeight - 8) top = r.top - 6 - alto >= 8 ? r.top - 6 - alto : Math.max(8, window.innerHeight - alto - 8)
  pos.value = { top, left: Math.max(8, Math.min(r.left, window.innerWidth - ancho - 8)), ancho }
}
const capa = abrirCapa()
function tecla(e) {
  if (e.key === 'Escape' && esLaDeArriba(capa)) {
    e.stopPropagation()
    emit('cerrar')
  }
}
function fuera(e) {
  if (raiz.value && !raiz.value.contains(e.target) && !props.ancla?.contains(e.target)) emit('cerrar')
}
onMounted(async () => {
  ubicar()
  window.addEventListener('resize', ubicar)
  window.addEventListener('scroll', ubicar, true)
  document.addEventListener('keydown', tecla)
  document.addEventListener('mousedown', fuera)
  await pedir()
  await nextTick()
  ubicar()
  buscador.value?.focus({ preventScroll: true })
})
onBeforeUnmount(() => {
  cerrarCapa(capa)
  clearTimeout(espera)
  window.removeEventListener('resize', ubicar)
  window.removeEventListener('scroll', ubicar, true)
  document.removeEventListener('keydown', tecla)
  document.removeEventListener('mousedown', fuera)
})
// Elegidos que la búsqueda actual no muestra (siguen marcados)
const ocultosMarcados = computed(() => [...marcados.value].filter((v) => !opciones.value.some((o) => o.valor === v)).length)
</script>

<template>
  <Teleport to="body">
    <div ref="raiz" class="fc" role="dialog" :aria-label="t('Filtrar por {0}', [titulo])"
         :style="{ top: `${pos.top}px`, left: `${pos.left}px`, width: `${pos.ancho}px` }">
      <div class="fc-titulo">{{ t('Filtrar por {0}', [titulo]) }}</div>
      <label class="buscador fc-buscar">
        <Icono nombre="buscar" :tam="15" />
        <input ref="buscador" v-model="q" class="entrada" type="search" :placeholder="t('Buscar valores…')" :aria-label="t('Buscar valores')"
               @input="buscar" @keydown.enter.prevent="aplicar" />
      </label>
      <div class="fc-lista" role="group" :aria-label="t('Valores')" :aria-busy="cargando">
        <label v-if="opciones.length > 1" class="fc-op fc-todos">
          <input type="checkbox" :checked="todos" @change="alternarTodos" />
          <span>{{ q ? t('(Elegir todos los resultados)') : t('(Elegir todos)') }}</span>
        </label>
        <label v-for="o in opciones" :key="o.valor" class="fc-op">
          <input type="checkbox" :checked="marcados.has(o.valor)" @change="alternar(o.valor)" />
          <span class="fc-texto" :class="{ apagado: o.valor === VACIO }">{{ o.texto }}</span>
          <span v-if="o.n !== undefined && o.n !== null" class="fc-n">{{ o.n }}</span>
        </label>
        <p v-if="!cargando && !opciones.length" class="ayuda fc-nada">{{ t('Ningún valor coincide.') }}</p>
        <p v-if="truncado" class="ayuda fc-nada">{{ t('Se muestran los primeros {0}; escriba para encontrar el resto.', [MAXIMO]) }}</p>
      </div>
      <p v-if="ocultosMarcados" class="ayuda fc-nota">{{ t('{0} elegidos más fuera de esta búsqueda.', [ocultosMarcados]) }}</p>
      <div class="fc-pie">
        <button type="button" class="btn btn-fantasma btn-chico" :disabled="!elegidos.length && !marcados.size" @click="limpiar">{{ t('Quitar') }}</button>
        <button type="button" class="btn btn-primario btn-chico" @click="aplicar">{{ t('Aplicar') }}</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.fc { position: fixed; z-index: 60; display: flex; flex-direction: column; gap: 8px; padding: 10px; max-height: min(460px, calc(100vh - 24px));
  background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio-panel); box-shadow: var(--sombra-flotante);
  font-size: 0.9rem; font-weight: 400; text-transform: none; letter-spacing: 0; color: var(--tinta); }
.fc-titulo { font-size: 0.86rem; font-weight: 600; color: var(--tinta-3); }
.fc-buscar, .fc-buscar input { width: 100%; min-width: 0 !important; }
.fc-lista { overflow: auto; min-height: 60px; max-height: 280px; margin: 0 -4px; }
.fc-op { display: flex; align-items: center; gap: 8px; padding: 5px 6px; border-radius: 6px; cursor: pointer; }
.fc-op:hover { background: var(--fila-hover); }
.fc-todos { font-weight: 600; border-bottom: 1px solid var(--linea-suave); border-radius: 0; margin-bottom: 2px; }
.fc-texto { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fc-n { font-size: 0.78rem; color: var(--tinta-3); font-variant-numeric: tabular-nums; }
.fc-nada, .fc-nota { margin: 4px 6px; }
.fc-pie { display: flex; justify-content: flex-end; gap: 6px; padding-top: 6px; border-top: 1px solid var(--linea-suave); }
</style>
