<script setup>
// Tabla y formulario de un catálogo simple, armados desde su definición (catalogos.js).
import { computed, onMounted, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import FilasEsqueleto from '@/componentes/FilasEsqueleto.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import { CATALOGOS } from './catalogos.js'

const props = defineProps({ ruta: { type: String, required: true } })
const emit = defineEmits(['cambio'])
const def = computed(() => CATALOGOS[props.ruta])
const filas = ref(null)
const fuentes = reactive({})
const transiciones = reactive({})
const editando = ref(null) // {id?, datos}
const errores = ref({})
const guardando = ref(false)
const busqueda = ref('')

const visibles = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!filas.value || !q) return filas.value
  return filas.value.filter((f) => `${f.codigo} ${f.nombre}`.toLowerCase().includes(q))
})
const conTransiciones = computed(() => def.value.campos.some((c) => c.tipo === 'transiciones'))

async function cargar() {
  try {
    filas.value = await catalogo(props.ruta, { recargar: true })
    for (const c of def.value.campos.filter((c) => c.fuente)) fuentes[c.fuente] = await catalogo(c.fuente)
    if (conTransiciones.value) {
      for (const f of filas.value) transiciones[f.id] = await api.get(`${CONFIG}/estados/${f.id}/transiciones`)
    }
  } catch (e) { avisarError(e); filas.value = [] }
}
onMounted(cargar)

function nombreDe(fuente, id) {
  const x = (fuentes[fuente] || []).find((f) => f.id === id)
  return x ? x.nombre : '—'
}

function abrir(fila = null) {
  errores.value = {}
  const datos = {}
  for (const c of def.value.campos) {
    if (c.tipo === 'transiciones') datos[c.campo] = fila ? [...(transiciones[fila.id] || [])] : []
    else datos[c.campo] = fila ? fila[c.campo] : c.defecto ?? (c.tipo === 'bool' ? false : null)
  }
  editando.value = { id: fila?.id ?? null, datos }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  try {
    const { transiciones: destinos, ...cuerpo } = editando.value.datos
    for (const c of def.value.campos) if (c.tipo === 'numero' && cuerpo[c.campo] === '') cuerpo[c.campo] = null
    const id = editando.value.id
    const r = id ? await api.patch(`${CONFIG}/${props.ruta}/${id}`, cuerpo) : await api.post(`${CONFIG}/${props.ruta}`, cuerpo)
    if (conTransiciones.value) await api.put(`${CONFIG}/estados/${r.id}/transiciones`, { destinos: destinos || [] })
    avisar(id ? 'Cambios guardados.' : `Se creó ${r.nombre}.`)
    editando.value = null
    invalidarCatalogo(props.ruta)
    await cargar()
    emit('cambio')
  } catch (e) {
    errores.value = e.porCampo
    avisarError(e)
  } finally { guardando.value = false }
}

async function borrar(fila) {
  const ok = await confirmar({ titulo: `Borrar ${def.value.singular}`, mensaje: `Se borrará «${fila.nombre}». Si está en uso no se podrá borrar: desactívelo en su lugar.`, accion: 'Borrar', peligro: true })
  if (!ok) return
  try {
    await api.del(`${CONFIG}/${props.ruta}/${fila.id}`)
    avisar('Registro borrado.')
    invalidarCatalogo(props.ruta)
    await cargar()
    emit('cambio')
  } catch (e) { avisarError(e) }
}

function alternarDestino(id) {
  const l = editando.value.datos.transiciones
  const i = l.indexOf(id)
  if (i >= 0) l.splice(i, 1)
  else l.push(id)
}
const NOMBRES = { codigo: 'Código', nombre: 'Nombre', activo: 'Activo', activa: 'Activa', orden: 'Orden', factor: 'Factor', decimales: 'Decimales', inicial: 'Inicial', operable: 'Operable', obligatoria: 'Obligatoria' }
const etiqueta = (c) => c.nombre || NOMBRES[c.campo] || c.campo.charAt(0).toUpperCase() + c.campo.slice(1).replaceAll('_', ' ')
</script>

<template>
  <section class="tarjeta">
    <header class="tarjeta-cabeza">
      <div>
        <h2>{{ def.titulo }}</h2>
        <p>{{ def.descripcion }}</p>
      </div>
      <div class="fila">
        <div class="busqueda">
          <Icono nombre="buscar" :tam="16" />
          <input v-model="busqueda" class="control" type="search" :aria-label="`Buscar en ${def.titulo.toLowerCase()}`" placeholder="Buscar" />
        </div>
        <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Agregar</button>
      </div>
    </header>
    <div class="tabla-envoltura">
      <table class="tabla">
        <thead>
          <tr>
            <th v-for="c in def.columnas" :key="c.campo" :class="{ derecha: c.tipo === 'numero' }">{{ etiqueta(c) }}</th>
            <th class="acciones"><span class="solo-lector">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <FilasEsqueleto v-if="filas === null" :columnas="def.columnas.length + 1" :filas="4" />
          <tr v-for="f in visibles || []" :key="f.id" class="clicable" @click="abrir(f)">
            <td v-for="c in def.columnas" :key="c.campo" :class="{ derecha: c.tipo === 'numero', num: c.tipo === 'numero' }">
              <code v-if="c.tipo === 'codigo'">{{ f[c.campo] || '—' }}</code>
              <span v-else-if="c.tipo === 'bool'" class="insignia sin-punto" :class="f[c.campo] ? 'ok' : ''">{{ f[c.campo] ? 'Sí' : 'No' }}</span>
              <span v-else-if="c.tipo === 'select'">{{ nombreDe(c.fuente, f[c.campo]) }}</span>
              <span v-else-if="c.tipo === 'transiciones'" class="fila envolver">
                <span v-for="d in transiciones[f.id] || []" :key="d" class="insignia sin-punto acento">{{ filas.find((x) => x.id === d)?.nombre }}</span>
                <span v-if="!(transiciones[f.id] || []).length" class="tenue chico">Cualquiera</span>
              </span>
              <span v-else>{{ f[c.campo] ?? '—' }}</span>
            </td>
            <td class="acciones" @click.stop>
              <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${f.nombre}`" @click="abrir(f)"><Icono nombre="editar" :tam="16" /></button>
              <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Borrar ${f.nombre}`" @click="borrar(f)"><Icono nombre="borrar" :tam="16" /></button>
            </td>
          </tr>
        </tbody>
      </table>
      <EstadoVacio v-if="filas && !filas.length" icono="cuadricula" :titulo="`Aún no hay ${def.titulo.toLowerCase()}`" texto="Agregue el primero para empezar.">
        <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Agregar</button>
      </EstadoVacio>
      <p v-else-if="filas && visibles && !visibles.length" class="tenue sin-resultados">Nada coincide con «{{ busqueda }}».</p>
    </div>

    <Modal v-if="editando" :titulo="editando.id ? `Editar ${def.singular}` : def.nuevo" @cerrar="editando = null">
      <form id="form-catalogo" class="pila" @submit.prevent="guardar">
        <template v-for="c in def.campos" :key="c.campo">
          <label v-if="c.tipo === 'bool'" class="pila-chica">
            <span class="interruptor"><input v-model="editando.datos[c.campo]" type="checkbox" />{{ etiqueta(c) }}</span>
            <span v-if="c.ayuda" class="tenue chico">{{ c.ayuda }}</span>
          </label>
          <div v-else-if="c.tipo === 'transiciones'" class="campo">
            <span class="etiqueta">{{ etiqueta(c) }}</span>
            <div class="fila envolver">
              <button v-for="d in filas.filter((x) => x.id !== editando.id)" :key="d.id" type="button" class="btn chico"
                      :class="{ primario: editando.datos.transiciones.includes(d.id) }" :aria-pressed="editando.datos.transiciones.includes(d.id)"
                      @click="alternarDestino(d.id)">{{ d.nombre }}</button>
            </div>
            <span class="ayuda">Sin elegir ninguno, puede pasar a cualquier estado.</span>
          </div>
          <Campo v-else :etiqueta="etiqueta(c)" :id="`f-${c.campo}`" :ayuda="c.ayuda" :error="errores[c.campo]" :obligatorio="c.obligatorio">
            <select v-if="c.tipo === 'select'" :id="`f-${c.campo}`" v-model="editando.datos[c.campo]" class="control" :class="{ invalido: errores[c.campo] }">
              <option :value="null" disabled>Elegir…</option>
              <option v-for="o in fuentes[c.fuente] || []" :key="o.id" :value="o.id">{{ o.nombre }}</option>
            </select>
            <input v-else :id="`f-${c.campo}`" v-model="editando.datos[c.campo]" class="control" :class="{ invalido: errores[c.campo], mono: c.tipo === 'codigo' }"
                   :type="c.tipo === 'numero' ? 'number' : 'text'" :step="c.tipo === 'numero' ? 'any' : undefined"
                   :required="c.obligatorio" :autocapitalize="c.tipo === 'codigo' ? 'characters' : undefined" />
          </Campo>
        </template>
      </form>
      <template #pie>
        <button class="btn" type="button" @click="editando = null">Cancelar</button>
        <button class="btn primario" type="submit" form="form-catalogo" :disabled="guardando">
          <span v-if="guardando" class="cargando-btn" />Guardar
        </button>
      </template>
    </Modal>
  </section>
</template>

<style scoped>
.busqueda { position: relative; width: 220px; }
.busqueda svg { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--tinta-3); pointer-events: none; }
.busqueda .control { padding-left: 32px; }
.sin-resultados { padding: var(--e-5); text-align: center; }
@media (max-width: 720px) { .busqueda { width: 100%; } .tarjeta-cabeza { flex-wrap: wrap; } }
</style>
