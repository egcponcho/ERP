<script setup>
// Catálogo: la tabla común (la misma de facturacion) en modo servidor. Cada
// columna ordena y se filtra por sus valores; además, búsqueda, categoría,
// filtros por cualquier característica («Más filtros») y los pendientes que
// manda el resumen del módulo (?pendiente=sin_codigos…).
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { claseEstado, fecha } from '@/nucleo/formato.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const router = useRouter()
const route = useRoute()
// Se puede llegar con un filtro de columna puesto (p. ej. desde un tipo: ?tipo=CALZADO)
const filtrosIniciales = Object.fromEntries(['tipo', 'estado', 'unidad'].filter((k) => route.query[k]).map((k) => [k, [].concat(route.query[k])]))
const filas = ref([])
const total = ref(0)
const cargando = ref(true)
const hayProductos = ref(true)
const tabla = ref(null)
const ext = reactive({ q: '', categoria_id: '', pendiente: route.query.pendiente || '' }) // filtros propios de la pantalla (se guardan en las vistas)
const PENDIENTES = { sin_codigos: 'Sin códigos', sin_presentaciones: 'Sin presentaciones', sin_categorias: 'Sin categoría' }
const porAtributo = ref([]) // [{ clave: 'a.peso__min', texto }]
const nuevoFiltro = ref({ codigo: '', operador: '', valor: '' })
const categorias = ref([])
const atributos = ref([])
let ultima = null
let espera = null

const COLUMNAS = [
  { clave: 'codigo', texto: 'Código', fija: true, filtro: false, prioridad: 1 },
  { clave: 'nombre', texto: 'Producto', filtro: false, prioridad: 1 },
  { clave: 'tipo', texto: 'Tipo', prioridad: 2 },
  { clave: 'estado', texto: 'Estado', prioridad: 1 },
  { clave: 'unidad', texto: 'Unidad', prioridad: 3 },
  { clave: 'variantes', texto: 'Variantes', num: true, filtro: false, ordenable: false, prioridad: 3 },
  { clave: 'actualizado', texto: 'Modificado', filtro: false, prioridad: 3 },
]

const paramsAtributos = () => Object.fromEntries(porAtributo.value.map((f) => [f.clave, f.valor]))
function parametros(c) {
  return { q: ext.q, categoria_id: ext.categoria_id, pendiente: ext.pendiente, ...paramsAtributos(), ...(c ? { orden: c.orden || 'codigo', pagina: c.page, tamano: c.size } : {}),
    ...Object.fromEntries(Object.entries(c?.filtros || ultima?.filtros || {})) }
}

async function consultar(c) {
  ultima = c
  cargando.value = true
  try {
    const r = await api.get('/productos', parametros(c))
    filas.value = r.datos
    total.value = r.total
    if (!r.total && !Object.keys(c.filtros).length && !ext.q && !ext.categoria_id && !ext.pendiente && !porAtributo.value.length) hayProductos.value = false
    else hayProductos.value = true
  } catch (e) { avisarError(e) } finally { cargando.value = false }
}
const reconsultar = () => ultima && consultar({ ...ultima, page: 1 })

async function valores(clave, q, otros) {
  return api.get(`/productos/valores/${clave}`, { buscar: q, q: ext.q, categoria_id: ext.categoria_id, pendiente: ext.pendiente, ...paramsAtributos(), ...otros })
}

function buscar() {
  clearTimeout(espera)
  espera = setTimeout(reconsultar, 300)
}

onMounted(async () => {
  try { ;[categorias.value, atributos.value] = await Promise.all([catalogo('categorias'), catalogo('atributos')]) } catch (e) { avisarError(e) }
})

// ---- Filtros por característica --------------------------------------------------------
const atributoFiltro = computed(() => atributos.value.find((a) => a.codigo === nuevoFiltro.value.codigo))
const operadores = computed(() => ['entero', 'decimal', 'fecha'].includes(atributoFiltro.value?.tipo_dato)
  ? [['', 'igual a'], ['min', 'desde'], ['max', 'hasta']] : [['', atributoFiltro.value?.tipo_dato === 'texto' ? 'contiene' : 'igual a']])
function agregarFiltro() {
  const f = nuevoFiltro.value
  const a = atributoFiltro.value
  if (!a || f.valor === '' || f.valor === null) return
  const clave = `a.${a.codigo}${f.operador ? `__${f.operador}` : ''}`
  const valorTxt = a.opciones?.find((o) => o.codigo === f.valor)?.nombre || (f.valor === 'si' ? 'Sí' : f.valor === 'no' ? 'No' : f.valor)
  const signo = { min: '≥', max: '≤' }[f.operador] || (a.tipo_dato === 'texto' ? 'contiene' : '=')
  porAtributo.value = [...porAtributo.value.filter((x) => x.clave !== clave), { clave, valor: f.valor, texto: `${a.nombre} ${signo} ${valorTxt}` }]
  nuevoFiltro.value = { codigo: '', operador: '', valor: '' }
  reconsultar()
}

const chips = computed(() => [
  ...(ext.pendiente ? [{ clave: 'pendiente', texto: PENDIENTES[ext.pendiente] || ext.pendiente }] : []),
  ...(ext.categoria_id ? [{ clave: 'categoria_id', texto: `Categoría: ${rutaCategoria(categorias.value.find((c) => c.id === Number(ext.categoria_id)))}` }] : []),
  ...porAtributo.value.map((f) => ({ clave: f.clave, texto: f.texto })),
])
function quitarExterno(clave) {
  if (clave === 'categoria_id') ext.categoria_id = ''
  else if (clave === 'pendiente') { ext.pendiente = ''; router.replace({ query: { ...route.query, pendiente: undefined } }) }
  else porAtributo.value = porAtributo.value.filter((f) => f.clave !== clave)
  reconsultar()
}
function limpiarExternos() {
  ext.q = ''
  ext.categoria_id = ''
  ext.pendiente = ''
  porAtributo.value = []
  reconsultar()
}
function aplicarVista(externos) {
  ext.q = externos.q || ''
  ext.categoria_id = externos.categoria_id || ''
  ext.pendiente = externos.pendiente || ''
  porAtributo.value = JSON.parse(externos._atributos || '[]')
}
const externos = computed(() => ({ q: ext.q, categoria_id: ext.categoria_id, pendiente: ext.pendiente, _atributos: porAtributo.value.length ? JSON.stringify(porAtributo.value) : '' }))

function rutaCategoria(c) {
  const r = []
  let x = c
  while (x) { r.unshift(x.nombre); x = categorias.value.find((p) => p.id === x.padre_id) }
  return r.join(' › ')
}
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div>
        <h1>Catálogo de productos</h1>
        <p>Busque por código, nombre o SKU. Ordene y filtre desde el encabezado de cada columna; para filtrar por una característica use «Más filtros».</p>
      </div>
    </header>

    <TablaDatos ref="tabla" tabla="productos" modo="servidor" :columnas="COLUMNAS" :filas="filas" :total="total" :cargando="cargando"
                orden-inicial="codigo:asc" :filtros-iniciales="filtrosIniciales" :valores="valores" fila-clicable etiqueta="Productos" :externos="externos" :chips-externos="chips"
                :mas-filtros-activos="porAtributo.length" @consulta="consultar" @fila="(f) => router.push(`/productos/${f.id}`)"
                @quitar-externo="quitarExterno" @limpiar-externos="limpiarExternos" @vista="aplicarVista">
      <template #barra>
        <label class="buscador">
          <Icono nombre="buscar" :tam="16" />
          <input v-model="ext.q" class="entrada" type="search" placeholder="Código, nombre o SKU" aria-label="Buscar productos" @input="buscar" />
        </label>
      </template>
      <template #filtros>
        <select v-if="categorias.length" v-model="ext.categoria_id" class="entrada" aria-label="Categoría" @change="reconsultar">
          <option value="">Todas las categorías</option>
          <option v-for="c in categorias" :key="c.id" :value="String(c.id)">{{ rutaCategoria(c) }}</option>
        </select>
      </template>
      <template #mas-filtros>
        <span class="ayuda">Por característica:</span>
        <select v-model="nuevoFiltro.codigo" class="entrada" aria-label="Característica" @change="nuevoFiltro.valor = ''; nuevoFiltro.operador = ''">
          <option value="">Elegir…</option>
          <option v-for="a in atributos" :key="a.id" :value="a.codigo">{{ a.nombre }}</option>
        </select>
        <select v-model="nuevoFiltro.operador" class="entrada" aria-label="Condición" :disabled="!atributoFiltro">
          <option v-for="[v, n] in operadores" :key="v" :value="v">{{ n }}</option>
        </select>
        <select v-if="['opcion', 'opciones'].includes(atributoFiltro?.tipo_dato)" v-model="nuevoFiltro.valor" class="entrada" aria-label="Valor">
          <option value="">Valor…</option>
          <option v-for="o in atributoFiltro.opciones" :key="o.codigo" :value="o.codigo">{{ o.nombre }}</option>
        </select>
        <select v-else-if="atributoFiltro?.tipo_dato === 'booleano'" v-model="nuevoFiltro.valor" class="entrada" aria-label="Valor">
          <option value="">Valor…</option><option value="si">Sí</option><option value="no">No</option>
        </select>
        <input v-else v-model="nuevoFiltro.valor" class="entrada" :type="atributoFiltro?.tipo_dato === 'fecha' ? 'date' : 'text'" aria-label="Valor"
               :placeholder="atributoFiltro?.magnitud_id ? `Ej.: 5 ${atributoFiltro.unidad_defecto || ''}` : 'Valor'" :disabled="!atributoFiltro" @keydown.enter="agregarFiltro" />
        <button type="button" class="btn btn-primario btn-chico" :disabled="!atributoFiltro || nuevoFiltro.valor === ''" @click="agregarFiltro">Aplicar</button>
      </template>

      <template #celda-codigo="{ fila }"><strong class="codigo">{{ fila.codigo }}</strong></template>
      <template #celda-nombre="{ fila }"><RouterLink :to="`/productos/${fila.id}`" class="enlace-doc principal-celda" @click.stop>{{ fila.nombre }}</RouterLink></template>
      <template #celda-tipo="{ fila }">{{ fila.tipo_nombre }}</template>
      <template #celda-estado="{ fila }"><span class="estado" :class="claseEstado({ operable: fila.operable, codigo: fila.estado })"><span class="estado-marca" />{{ fila.estado_nombre }}</span></template>
      <template #celda-variantes="{ fila }">{{ fila.variantes || '—' }}</template>
      <template #celda-actualizado="{ fila }"><span class="apagado">{{ fecha(fila.actualizado_en) }}</span></template>
      <template #acciones="{ fila }"><RouterLink :to="`/productos/${fila.id}`" class="btn btn-chico btn-fantasma" @click.stop>Abrir<Icono nombre="derecha" :tam="14" /></RouterLink></template>
      <template #vacio>
        <EstadoVacio v-if="!hayProductos" icono="caja" titulo="Todavía no hay productos"
                     texto="El asistente lo guía paso a paso: elige el tipo, completa sus datos y características, y genera sus variantes."
                     :requisitos="['Un tipo de producto (se puede crear en el mismo asistente)', 'Su nombre y unidad']" titulo-requisitos="Necesita:">
          <RouterLink class="btn btn-primario" to="/productos/nuevo"><Icono nombre="mas" :tam="16" />Crear el primer producto</RouterLink>
        </EstadoVacio>
        <template v-else>No hay productos con estos filtros.</template>
      </template>
    </TablaDatos>
  </div>
</template>
