<script setup>
// Categorías: se elige la taxonomía (pastillas) y su árbol se ve en la tabla común
// con sangría; cada fila se abre para editarla y desde ella se agrega una subcategoría.
import { computed, onMounted, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const taxonomias = ref([])
const categorias = ref([])
const elegida = ref(null)
const cargando = ref(true)
const nueva = ref(null) // { padre_id, nombre, codigo }
const nuevaTax = ref(null)
const edicion = reactive({})
const error = ref('')

async function cargar() {
  cargando.value = true
  try {
    ;[taxonomias.value, categorias.value] = await Promise.all([catalogo('taxonomias', { recargar: true }), catalogo('categorias', { recargar: true })])
    if (!taxonomias.value.some((t) => t.id === elegida.value)) elegida.value = taxonomias.value[0]?.id ?? null
  } catch (e) { avisarError(e) } finally { cargando.value = false }
}
onMounted(cargar)
const taxonomia = computed(() => taxonomias.value.find((t) => t.id === elegida.value))
const cuenta = (id) => categorias.value.filter((c) => c.taxonomia_id === id).length

const filas = computed(() => {
  const hijos = {}
  for (const c of categorias.value.filter((x) => x.taxonomia_id === elegida.value)) (hijos[c.padre_id ?? 0] ||= []).push(c)
  const res = []
  const visitar = (padre, nivel, ruta) => {
    for (const c of (hijos[padre] || []).sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre))) {
      res.push({ ...c, nivel, ruta: [...ruta, c.nombre].join(' › '), hijos: (hijos[c.id] || []).length })
      visitar(c.id, nivel + 1, [...ruta, c.nombre])
    }
  }
  visitar(0, 0, [])
  return res
})
const COLUMNAS = [
  { clave: 'nombre', texto: 'Categoría', fija: true, valor: (f) => f.ruta, ordenable: false },
  { clave: 'codigo', texto: 'Código', ordenable: false },
  { clave: 'hijos', texto: 'Subcategorías', num: true, filtro: false, ordenable: false },
  { clave: 'activa', texto: 'Activa', valor: (f) => f.activa, textoValor: (v) => (v ? 'Sí' : 'No'), ordenable: false },
]
const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 30)

function agregar(padre = null) {
  error.value = ''
  nueva.value = { padre_id: padre?.id ?? null, padre: padre?.ruta, nombre: '', codigo: '', tocado: false }
}
async function crear() {
  error.value = ''
  try {
    await api.post(`${CONFIG}/categorias`, { taxonomia_id: elegida.value, padre_id: nueva.value.padre_id, nombre: nueva.value.nombre, codigo: nueva.value.codigo })
    avisar(`Se creó ${nueva.value.nombre}.`)
    invalidarCatalogo('categorias')
    nueva.value = { ...nueva.value, nombre: '', codigo: '', tocado: false } // listo para la siguiente
    await cargar()
  } catch (e) { error.value = e.message }
}
function abrir(c) {
  edicion[c.id] = { nombre: c.nombre, codigo: c.codigo, padre_id: c.padre_id, orden: c.orden, activa: c.activa, error: '' }
}
async function guardar(c) {
  const e = edicion[c.id]
  e.error = ''
  try {
    await api.patch(`${CONFIG}/categorias/${c.id}`, { nombre: e.nombre, codigo: e.codigo, padre_id: e.padre_id, orden: Number(e.orden) || 0, activa: e.activa })
    avisar('Categoría guardada.')
    invalidarCatalogo('categorias')
    await cargar()
  } catch (err) { e.error = err.message }
}
async function borrar(c) {
  try {
    await api.del(`${CONFIG}/categorias/${c.id}`)
    avisar(`Se borró ${c.nombre}.`)
    invalidarCatalogo('categorias')
    await cargar()
  } catch (e) { avisarError(e) }
}
async function crearTaxonomia() {
  error.value = ''
  try {
    const t = await api.post(`${CONFIG}/taxonomias`, { nombre: nuevaTax.value.nombre, codigo: norm(nuevaTax.value.nombre), multiple: nuevaTax.value.multiple, obligatoria: nuevaTax.value.obligatoria })
    avisar(`Se creó la taxonomía ${t.nombre}.`)
    invalidarCatalogo('taxonomias')
    nuevaTax.value = null
    await cargar()
    elegida.value = t.id
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div>
    <div class="seccion-cabeza"><h2>Categorías</h2>
      <p class="ayuda">Agrupe sus productos de varias formas a la vez: cada taxonomía (línea comercial, familia contable, canal…) es un árbol independiente.</p></div>

    <div class="fila-flex mb-3">
      <div v-if="taxonomias.length" class="pestanas-pildora mb-0" role="tablist" aria-label="Taxonomías">
        <button v-for="t in taxonomias" :key="t.id" type="button" role="tab" class="pildora" :aria-selected="t.id === elegida" @click="elegida = t.id; nueva = null">
          {{ t.nombre }}<span class="cuenta">{{ cuenta(t.id) }}</span></button>
      </div>
      <button v-if="!nuevaTax" type="button" class="btn btn-chico" @click="nuevaTax = { nombre: '', multiple: false, obligatoria: false }"><Icono nombre="mas" :tam="14" />Taxonomía</button>
      <RouterLink class="btn btn-chico btn-fantasma separar" to="/productos/configuracion/taxonomias">Administrar taxonomías</RouterLink>
    </div>

    <PanelEnLinea v-if="nuevaTax" titulo="Nueva taxonomía" @cerrar="nuevaTax = null">
      <p v-if="error" class="nota error mb-3">{{ error }}</p>
      <div class="rejilla-campos">
        <label class="campo"><span class="req">Nombre</span><input v-model="nuevaTax.nombre" class="entrada" placeholder="Línea comercial" autofocus @keydown.enter.prevent="crearTaxonomia" /></label>
        <label class="check"><input v-model="nuevaTax.multiple" type="checkbox" />Un producto puede estar en varias categorías</label>
        <label class="check"><input v-model="nuevaTax.obligatoria" type="checkbox" />Obligatoria para activar un producto</label>
      </div>
      <template #pie><button type="button" class="btn" @click="nuevaTax = null">Cancelar</button>
        <button type="button" class="btn btn-primario" :disabled="!nuevaTax.nombre.trim()" @click="crearTaxonomia">Crear</button></template>
    </PanelEnLinea>

    <template v-if="taxonomia">
      <PanelEnLinea v-if="nueva" :titulo="nueva.padre ? `Nueva subcategoría de ${nueva.padre}` : `Nueva categoría en ${taxonomia.nombre}`"
                    descripcion="Al crearla, el formulario queda listo para la siguiente." @cerrar="nueva = null">
        <p v-if="error" class="nota error mb-3">{{ error }}</p>
        <div class="rejilla-campos">
          <label class="campo"><span class="req">Nombre</span><input v-model="nueva.nombre" class="entrada" autofocus @input="!nueva.tocado && (nueva.codigo = norm(nueva.nombre))" @keydown.enter.prevent="crear" /></label>
          <label class="campo"><span class="req">Código</span><input v-model="nueva.codigo" class="entrada mono" maxlength="30" @input="nueva.tocado = true" /></label>
        </div>
        <template #pie><button type="button" class="btn" @click="nueva = null">Listo</button>
          <button type="button" class="btn btn-primario" :disabled="!nueva.nombre.trim()" @click="crear"><Icono nombre="mas" :tam="16" />Agregar</button></template>
      </PanelEnLinea>
      <TablaDatos :key="elegida" :tabla="`config-categorias`" :columnas="COLUMNAS" :filas="filas" :cargando="cargando" expandible :etiqueta="taxonomia.nombre" @expandir="abrir">
        <template #barra><button v-if="!nueva" type="button" class="btn btn-primario" @click="agregar()"><Icono nombre="mas" :tam="16" />Nueva categoría</button></template>
        <template #celda-nombre="{ fila }"><span class="arbol" :style="{ paddingInlineStart: `${fila.nivel * 22}px` }">
          <Icono v-if="fila.nivel" nombre="heredado" :tam="13" class="apagado" /><b :class="{ apagado: !fila.activa }">{{ fila.nombre }}</b></span></template>
        <template #celda-codigo="{ fila }"><code>{{ fila.codigo }}</code></template>
        <template #celda-hijos="{ fila }">{{ fila.hijos || '—' }}</template>
        <template #celda-activa="{ fila }"><span class="estado" :class="fila.activa ? 'estado-ok' : 'estado-neutro'"><span class="estado-marca" />{{ fila.activa ? 'Sí' : 'No' }}</span></template>
        <template #acciones="{ fila }">
          <button type="button" class="btn btn-chico btn-fantasma" @click="agregar(fila)"><Icono nombre="mas" :tam="13" />Subcategoría</button>
          <BotonConfirmar :etiqueta="`Borrar ${fila.nombre}`" @confirmar="borrar(fila)" />
        </template>
        <template #detalle="{ fila }">
          <form v-if="edicion[fila.id]" class="edicion" @submit.prevent="guardar(fila)">
            <p v-if="edicion[fila.id].error" class="nota error">{{ edicion[fila.id].error }}</p>
            <div class="rejilla-campos">
              <label class="campo"><span class="req">Nombre</span><input v-model="edicion[fila.id].nombre" class="entrada" /></label>
              <label class="campo"><span class="req">Código</span><input v-model="edicion[fila.id].codigo" class="entrada mono" /></label>
              <label class="campo"><span>Dentro de</span>
                <select v-model="edicion[fila.id].padre_id" class="entrada"><option :value="null">Nivel principal</option>
                  <option v-for="c in filas.filter((x) => x.id !== fila.id)" :key="c.id" :value="c.id">{{ c.ruta }}</option></select></label>
              <label class="campo"><span>Orden</span><input v-model="edicion[fila.id].orden" class="entrada num ancho-s" type="number" /></label>
              <label class="check"><input v-model="edicion[fila.id].activa" type="checkbox" />Activa</label>
            </div>
            <div class="fila-flex"><button type="submit" class="btn btn-primario btn-chico"><Icono nombre="check" :tam="14" />Guardar</button></div>
          </form>
        </template>
        <template #vacio>{{ taxonomia.nombre }} no tiene categorías. <button type="button" class="btn-texto" @click="agregar()">Crear la primera</button></template>
      </TablaDatos>
    </template>
    <p v-else-if="!cargando" class="nota info"><Icono nombre="info" :tam="16" /><span>Primero cree una taxonomía, por ejemplo «Línea comercial».</span></p>
  </div>
</template>

<style scoped>
.seccion-cabeza { margin-bottom: 14px; }
.arbol { display: inline-flex; align-items: center; gap: 6px; }
.edicion { display: flex; flex-direction: column; gap: 10px; }
</style>
