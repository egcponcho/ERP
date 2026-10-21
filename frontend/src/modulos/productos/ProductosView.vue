<script setup>
// Lista de productos con búsqueda, filtros por tipo, estado, categoría y cualquier atributo.
// Los filtros viven en la URL: se pueden compartir y sobreviven a recargar la página.
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import FilasEsqueleto from '@/componentes/FilasEsqueleto.vue'
import Icono from '@/componentes/Icono.vue'
import Paginacion from '@/componentes/Paginacion.vue'
import NuevoProducto from './NuevoProducto.vue'

const route = useRoute()
const router = useRouter()
const resultado = ref(null)
const tipos = ref([])
const estados = ref([])
const categorias = ref([])
const atributos = ref([])
const texto = ref(route.query.q || '')
const filtroAtributo = ref(null) // {codigo, operador, valor}
const nuevo = ref(route.query.nuevo === '1')
let espera = null

const q = computed(() => route.query)
const filtrosAtributo = computed(() => Object.entries(q.value).filter(([k]) => k.startsWith('a.'))
  .map(([k, v]) => {
    const [codigo, op] = k.slice(2).split('__')
    return { clave: k, codigo, op, valor: v, atributo: atributos.value.find((a) => a.codigo === codigo) }
  }))
const hayFiltros = computed(() => !!(q.value.q || q.value.tipo_id || q.value.estado_id || q.value.categoria_id || filtrosAtributo.value.length))

async function cargar() {
  resultado.value = null
  try {
    resultado.value = await api.get('/productos', { ...q.value, nuevo: undefined, tamano: 25 })
  } catch (e) { avisarError(e); resultado.value = { total: 0, datos: [], pagina: 1, tamano: 25 } }
}

onMounted(async () => {
  try {
    ;[tipos.value, estados.value, categorias.value, atributos.value] = await Promise.all([
      catalogo('tipos-producto'), catalogo('estados'), catalogo('categorias'), catalogo('atributos')])
  } catch (e) { avisarError(e) }
})
watch(() => route.fullPath, () => { if (route.name === 'productos') cargar() }, { immediate: true })

function fijar(cambios) {
  const query = { ...q.value, ...cambios, pagina: cambios.pagina ?? undefined }
  for (const k of Object.keys(query)) if (query[k] === '' || query[k] === null || query[k] === undefined) delete query[k]
  delete query.nuevo
  router.replace({ query })
}
watch(texto, (t) => { clearTimeout(espera); espera = setTimeout(() => fijar({ q: t.trim() }), 300) })

function limpiar() {
  texto.value = ''
  router.replace({ query: {} })
}
function agregarFiltro() {
  const f = filtroAtributo.value
  if (!f?.codigo || f.valor === '' || f.valor === null) return
  fijar({ [`a.${f.codigo}${f.operador ? `__${f.operador}` : ''}`]: Array.isArray(f.valor) ? f.valor.join(',') : f.valor })
  filtroAtributo.value = null
}
const atributoFiltro = computed(() => atributos.value.find((a) => a.codigo === filtroAtributo.value?.codigo))
const operadores = computed(() => ['entero', 'decimal', 'fecha'].includes(atributoFiltro.value?.tipo_dato)
  ? [{ v: '', n: 'igual a' }, { v: 'min', n: 'desde' }, { v: 'max', n: 'hasta' }] : [{ v: '', n: atributoFiltro.value?.tipo_dato === 'texto' ? 'contiene' : 'igual a' }])
const opNombre = { min: '≥', max: '≤' }

const nombreTipo = (codigo) => tipos.value.find((t) => t.codigo === codigo)?.nombre || codigo
const estado = (codigo) => estados.value.find((e) => e.codigo === codigo)
function tono(codigo) {
  const e = estado(codigo)
  if (!e) return ''
  return e.operable ? 'ok' : e.inicial ? 'info' : ''
}
const rutaCategoria = (c) => {
  const r = []
  let x = c
  while (x) { r.unshift(x.nombre); x = categorias.value.find((p) => p.id === x.padre_id) }
  return r.join(' › ')
}
</script>

<template>
  <div class="pagina">
    <header class="pagina-cabeza">
      <div>
        <h1>Productos</h1>
        <p>Todos los productos, de cualquier rubro. Filtre por tipo, estado, categoría o cualquier característica.</p>
      </div>
      <button class="btn primario" type="button" @click="nuevo = true"><Icono nombre="mas" :tam="16" />Nuevo producto</button>
    </header>

    <section class="tarjeta">
      <div class="filtros">
        <div class="busqueda">
          <Icono nombre="buscar" :tam="16" />
          <input v-model="texto" class="control" type="search" placeholder="Buscar por código, nombre o SKU" aria-label="Buscar productos" />
        </div>
        <select class="control" :value="q.tipo_id || ''" aria-label="Tipo de producto" @change="fijar({ tipo_id: $event.target.value })">
          <option value="">Todos los tipos</option>
          <option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option>
        </select>
        <select class="control" :value="q.estado_id || ''" aria-label="Estado" @change="fijar({ estado_id: $event.target.value })">
          <option value="">Todos los estados</option>
          <option v-for="e in estados" :key="e.id" :value="e.id">{{ e.nombre }}</option>
        </select>
        <select v-if="categorias.length" class="control" :value="q.categoria_id || ''" aria-label="Categoría" @change="fijar({ categoria_id: $event.target.value })">
          <option value="">Todas las categorías</option>
          <option v-for="c in categorias" :key="c.id" :value="c.id">{{ rutaCategoria(c) }}</option>
        </select>
        <button class="btn" type="button" :aria-expanded="!!filtroAtributo" @click="filtroAtributo = filtroAtributo ? null : { codigo: '', operador: '', valor: '' }">
          <Icono nombre="ajustes" :tam="16" />Filtrar por atributo
        </button>
      </div>

      <div v-if="filtroAtributo" class="constructor">
        <select v-model="filtroAtributo.codigo" class="control" aria-label="Atributo" @change="filtroAtributo.valor = ''; filtroAtributo.operador = ''">
          <option value="" disabled>Atributo…</option>
          <option v-for="a in atributos" :key="a.id" :value="a.codigo">{{ a.nombre }}</option>
        </select>
        <select v-model="filtroAtributo.operador" class="control op" aria-label="Condición" :disabled="!atributoFiltro">
          <option v-for="o in operadores" :key="o.v" :value="o.v">{{ o.n }}</option>
        </select>
        <select v-if="['opcion', 'opciones'].includes(atributoFiltro?.tipo_dato)" v-model="filtroAtributo.valor" class="control" aria-label="Valor">
          <option value="" disabled>Valor…</option>
          <option v-for="o in atributoFiltro.opciones" :key="o.codigo" :value="o.codigo">{{ o.nombre }}</option>
        </select>
        <select v-else-if="atributoFiltro?.tipo_dato === 'booleano'" v-model="filtroAtributo.valor" class="control" aria-label="Valor">
          <option value="si">Sí</option><option value="no">No</option>
        </select>
        <input v-else v-model="filtroAtributo.valor" class="control" :type="atributoFiltro?.tipo_dato === 'fecha' ? 'date' : 'text'" aria-label="Valor"
               :placeholder="atributoFiltro?.magnitud_id ? `Ej.: 5 ${atributoFiltro.unidad_defecto || ''}` : 'Valor'" :disabled="!atributoFiltro" @keydown.enter="agregarFiltro" />
        <button class="btn primario" type="button" :disabled="!atributoFiltro || filtroAtributo.valor === ''" @click="agregarFiltro">Aplicar</button>
      </div>

      <div v-if="hayFiltros" class="activos">
        <span v-for="f in filtrosAtributo" :key="f.clave" class="chip">
          {{ f.atributo?.nombre || f.codigo }} {{ opNombre[f.op] || (f.atributo?.tipo_dato === 'texto' ? '∋' : '=') }}
          {{ f.atributo?.opciones?.find((o) => o.codigo === f.valor)?.nombre || f.valor }}
          <button type="button" :aria-label="`Quitar filtro ${f.atributo?.nombre || f.codigo}`" @click="fijar({ [f.clave]: undefined })"><Icono nombre="cerrar" :tam="12" /></button>
        </span>
        <button class="btn fantasma chico" type="button" @click="limpiar">Limpiar filtros</button>
      </div>

      <div class="tabla-envoltura">
        <table class="tabla">
          <thead><tr><th>Código</th><th>Producto</th><th>Tipo</th><th>Unidad</th><th class="derecha">Variantes</th><th>Estado</th></tr></thead>
          <tbody>
            <FilasEsqueleto v-if="!resultado" :columnas="6" :filas="8" />
            <tr v-for="p in resultado?.datos || []" :key="p.id" class="clicable" @click="router.push(`/productos/${p.id}`)">
              <td><code>{{ p.codigo }}</code></td>
              <td><RouterLink :to="`/productos/${p.id}`" class="nombre" @click.stop>{{ p.nombre }}</RouterLink></td>
              <td class="tenue">{{ nombreTipo(p.tipo) }}</td>
              <td class="tenue">{{ p.unidad }}</td>
              <td class="derecha num">{{ p.variantes || '—' }}</td>
              <td><span class="insignia" :class="tono(p.estado)">{{ estado(p.estado)?.nombre || p.estado }}</span></td>
            </tr>
          </tbody>
        </table>
        <EstadoVacio v-if="resultado && !resultado.total && !hayFiltros" titulo="Aún no hay productos"
                     texto="Cree su primer producto: elija un tipo y el formulario se arma solo con sus atributos.">
          <button class="btn primario" type="button" @click="nuevo = true"><Icono nombre="mas" :tam="16" />Nuevo producto</button>
        </EstadoVacio>
        <EstadoVacio v-else-if="resultado && !resultado.total" icono="buscar" titulo="Ningún producto coincide" texto="Pruebe con otros filtros.">
          <button class="btn" type="button" @click="limpiar">Limpiar filtros</button>
        </EstadoVacio>
      </div>
      <Paginacion v-if="resultado?.total" :pagina="resultado.pagina" :tamano="resultado.tamano" :total="resultado.total" @cambiar="fijar({ pagina: $event })" />
    </section>

    <NuevoProducto v-if="nuevo" @cerrar="nuevo = false" />
  </div>
</template>

<style scoped>
.filtros { display: flex; gap: var(--e-3); padding: var(--e-4); flex-wrap: wrap; border-bottom: 1px solid var(--linea); }
.filtros > select { width: auto; min-width: 160px; }
.busqueda { position: relative; flex: 1; min-width: 240px; }
.busqueda svg { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--tinta-3); pointer-events: none; }
.busqueda .control { padding-left: 32px; }
.constructor { display: flex; gap: var(--e-2); padding: var(--e-3) var(--e-4); background: var(--superficie-2); border-bottom: 1px solid var(--linea); flex-wrap: wrap; }
.constructor > * { width: auto; min-width: 150px; }
.constructor .op { min-width: 110px; }
.activos { display: flex; gap: var(--e-2); flex-wrap: wrap; align-items: center; padding: var(--e-3) var(--e-4); border-bottom: 1px solid var(--linea); }
.nombre { color: var(--tinta); font-weight: 550; }
</style>
