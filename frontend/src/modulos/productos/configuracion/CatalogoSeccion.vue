<script setup>
// Un catálogo simple: el formulario a la izquierda y la tabla común a la derecha
// (el patrón de mantenimiento de facturacion). Elegir una fila la carga en el
// formulario; «Nuevo» lo deja en blanco. Nada se abre en ventanas.
import { computed, onMounted, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo as leerCatalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'
import { CATALOGOS } from './catalogos.js'

const props = defineProps({ catalogo: { type: String, required: true } })
const def = computed(() => CATALOGOS[props.catalogo])
const filas = ref([])
const cargando = ref(true)
const fuentes = reactive({})
const transiciones = reactive({})
const form = ref(null) // { id, datos }
const errores = ref({})
const ocupado = ref(false)
const conTransiciones = computed(() => def.value?.campos.some((c) => c.tipo === 'transiciones'))

const columnas = computed(() => (def.value?.columnas || []).map((c) => (c.fuente
  ? { ...c, valor: (f) => (fuentes[c.fuente] || []).find((x) => x.id === f[c.clave])?.nombre } : c)))

async function cargar() {
  cargando.value = true
  try {
    filas.value = await leerCatalogo(props.catalogo, { recargar: true })
    for (const c of def.value.campos.filter((x) => x.fuente)) fuentes[c.fuente] = await leerCatalogo(c.fuente)
    if (conTransiciones.value) await Promise.all(filas.value.map(async (f) => { transiciones[f.id] = await api.get(`${CONFIG}/estados/${f.id}/transiciones`) }))
  } catch (e) { avisarError(e) } finally { cargando.value = false }
}
onMounted(async () => { await cargar(); nuevo() })

function nuevo() {
  errores.value = {}
  form.value = { id: null, datos: Object.fromEntries(def.value.campos.map((c) => [c.campo, c.tipo === 'transiciones' ? [] : c.defecto ?? (c.tipo === 'bool' ? false : c.tipo === 'select' ? null : '')])) }
}
function elegir(f) {
  errores.value = {}
  form.value = { id: f.id, datos: Object.fromEntries(def.value.campos.map((c) => [c.campo, c.tipo === 'transiciones' ? [...(transiciones[f.id] || [])] : f[c.campo] ?? (c.tipo === 'bool' ? false : '')])) }
}
const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '')
function alNombre() {
  if (form.value.id || form.value.codigoTocado) return
  form.value.datos.codigo = norm(form.value.datos.nombre).toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 20)
}

async function guardar() {
  ocupado.value = true
  errores.value = {}
  const { transiciones: destinos, ...cuerpo } = form.value.datos
  for (const c of def.value.campos) {
    if (c.tipo === 'numero') cuerpo[c.campo] = cuerpo[c.campo] === '' || cuerpo[c.campo] === null ? null : Number(cuerpo[c.campo])
    else if (c.tipo !== 'bool' && c.tipo !== 'select' && c.tipo !== 'transiciones' && cuerpo[c.campo] === '' && !c.obligatorio) cuerpo[c.campo] = null
  }
  try {
    const id = form.value.id
    const r = id ? await api.patch(`${CONFIG}/${props.catalogo}/${id}`, cuerpo) : await api.post(`${CONFIG}/${props.catalogo}`, cuerpo)
    if (conTransiciones.value) await api.put(`${CONFIG}/estados/${r.id}/transiciones`, { destinos: destinos || [] })
    avisar(id ? 'Cambios guardados.' : `Se creó ${r.nombre}.`)
    invalidarCatalogo(props.catalogo)
    await cargar()
    if (id) elegir(filas.value.find((f) => f.id === id))
    else nuevo()
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { ocupado.value = false }
}
async function borrar() {
  try {
    await api.del(`${CONFIG}/${props.catalogo}/${form.value.id}`)
    avisar('Registro borrado.')
    invalidarCatalogo(props.catalogo)
    await cargar()
    nuevo()
  } catch (e) { avisarError(e) }
}
function alternarDestino(id) {
  const l = form.value.datos.transiciones
  const i = l.indexOf(id)
  if (i >= 0) l.splice(i, 1)
  else l.push(id)
}
const nombreEstado = (id) => filas.value.find((x) => x.id === id)?.nombre
</script>

<template>
  <div v-if="def">
    <div class="seccion-cabeza"><h2>{{ def.titulo }}</h2><p class="ayuda">{{ def.descripcion }}</p></div>
    <div class="mantenimiento">
      <form v-if="form" class="panel form-catalogo" @submit.prevent="guardar">
        <div class="fila-flex entre">
          <h3>{{ form.id ? `Editar ${def.singular}` : def.nuevo }}</h3>
          <button v-if="form.id" type="button" class="btn btn-chico btn-fantasma" @click="nuevo"><Icono nombre="mas" :tam="14" />Nuevo</button>
        </div>
        <p v-if="errores._general" class="nota error">{{ errores._general }}</p>
        <template v-for="c in def.campos" :key="c.campo">
          <label v-if="c.tipo === 'bool'" class="check"><input v-model="form.datos[c.campo]" type="checkbox" />{{ c.nombre }}</label>
          <small v-if="c.tipo === 'bool' && c.ayuda" class="ayuda ayuda-check">{{ c.ayuda }}</small>
          <div v-else-if="c.tipo === 'transiciones'" class="campo"><span>{{ c.nombre }}</span>
            <div class="opciones-chips">
              <button v-for="d in filas.filter((x) => x.id !== form.id)" :key="d.id" type="button" class="opcion-chip"
                      :aria-pressed="form.datos.transiciones.includes(d.id)" @click="alternarDestino(d.id)">{{ d.nombre }}</button>
            </div>
            <small class="ayuda">Sin elegir ninguno puede pasar a cualquier estado.</small></div>
          <label v-else-if="c.tipo !== 'bool'" class="campo" :class="{ 'con-error': errores[c.campo] }"><span :class="{ req: c.obligatorio }">{{ c.nombre }}</span>
            <select v-if="c.tipo === 'select'" v-model="form.datos[c.campo]" class="entrada">
              <option :value="null" disabled>Elegir…</option>
              <option v-for="o in fuentes[c.fuente] || []" :key="o.id" :value="o.id">{{ o.nombre }}</option>
            </select>
            <input v-else v-model="form.datos[c.campo]" class="entrada" :class="{ mono: c.tipo === 'codigo' }" :type="c.tipo === 'numero' ? 'number' : 'text'"
                   step="any" :required="c.obligatorio" @input="c.campo === 'nombre' ? alNombre() : c.campo === 'codigo' ? (form.codigoTocado = true) : null" />
            <small v-if="errores[c.campo]" class="campo-error">{{ errores[c.campo] }}</small>
            <small v-else-if="c.ayuda" class="ayuda">{{ c.ayuda }}</small></label>
        </template>
        <div class="fila-flex">
          <BotonConfirmar v-if="form.id" :etiqueta="`Borrar ${form.datos.nombre}`" texto="Borrar" pregunta="¿Borrar? Si está en uso, desactívelo." @confirmar="borrar" />
          <button type="submit" class="btn btn-primario separar" :disabled="ocupado"><Icono nombre="check" :tam="16" />{{ form.id ? 'Guardar' : 'Agregar' }}</button>
        </div>
      </form>
      <TablaDatos :tabla="`config-${catalogo}`" :columnas="columnas" :filas="filas" :cargando="cargando" fila-clicable :fila-activa="form?.id"
                  :etiqueta="def.titulo" @fila="elegir">
        <template v-for="c in def.columnas.filter((x) => x.textoValor)" :key="c.clave" #[`celda-${c.clave}`]="{ fila }">
          <span class="estado" :class="fila[c.clave] ? 'estado-ok' : 'estado-neutro'"><span class="estado-marca" />{{ fila[c.clave] ? 'Sí' : 'No' }}</span></template>
        <template #celda-codigo="{ fila }"><code>{{ fila.codigo }}</code></template>
        <template #celda-nombre="{ fila }"><b>{{ fila.nombre }}</b></template>
        <template #celda-patron="{ fila }"><code>{{ fila.patron || '—' }}</code></template>
        <template #celda-magnitud_id="{ fila }">{{ (fuentes.magnitudes || []).find((m) => m.id === fila.magnitud_id)?.nombre }}</template>
        <template #celda-transiciones="{ fila }">
          <span v-if="(transiciones[fila.id] || []).length" class="insignias mt-0"><span v-for="d in transiciones[fila.id]" :key="d" class="etiqueta acento ms-0">{{ nombreEstado(d) }}</span></span>
          <span v-else class="apagado">Cualquiera</span></template>
        <template #vacio>Todavía no hay registros. Use el formulario de la izquierda.</template>
      </TablaDatos>
    </div>
  </div>
  <p v-else class="ayuda">Este apartado no existe.</p>
</template>

<style scoped>
.seccion-cabeza { margin-bottom: 14px; }
.seccion-cabeza p { margin-top: 2px; }
.form-catalogo { position: sticky; top: 76px; }
.ayuda-check { margin-top: -8px; padding-inline-start: 24px; }
</style>
