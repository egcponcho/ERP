<script setup>
// Variantes (SKU): tabla con los valores de sus ejes, alta individual, edición y
// generación de todas las combinaciones de los ejes con vista previa.
import { computed, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { valorTexto } from '@/nucleo/formato.js'
import Campo from '@/componentes/Campo.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'

const props = defineProps({ producto: { type: Object, required: true }, esquema: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const ejes = computed(() => props.esquema.campos.filter((c) => c.es_eje))
const otros = computed(() => props.esquema.campos.filter((c) => c.nivel === 'variante' && !c.es_eje))
const columnas = computed(() => [...ejes.value, ...otros.value])
const busqueda = ref('')
const editando = ref(null) // {id?, version?, codigo, nombre, activa, atributos}
const generando = ref(null) // {ejes: {codigo: [valores]}, texto: {codigo: ''}}
const resultado = ref(null)
const errores = ref({})
const general = ref(null)
const guardando = ref(false)

const visibles = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  if (!q) return props.producto.variantes
  return props.producto.variantes.filter((v) => `${v.codigo} ${v.nombre} ${Object.values(v.atributos).flat().join(' ')}`.toLowerCase().includes(q))
})

function abrir(v = null) {
  errores.value = {}
  general.value = null
  const atributos = {}
  for (const c of columnas.value) {
    if (v) atributos[c.atributo.codigo] = JSON.parse(JSON.stringify(v.atributos[c.atributo.codigo] ?? null))
    else if (c.valor_defecto !== null && c.valor_defecto !== undefined) atributos[c.atributo.codigo] = c.valor_defecto
  }
  editando.value = v ? { id: v.id, version: v.version, codigo: v.codigo, nombre: v.nombre, activa: v.activa, atributos }
    : { codigo: '', nombre: '', activa: true, atributos }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  general.value = null
  const e = editando.value
  const atributos = Object.fromEntries(Object.entries(e.atributos).map(([k, v]) => [k, v === '' || (Array.isArray(v) && !v.length) ? null : v]))
  try {
    if (e.id) await api.patch(`/productos/${props.producto.id}/variantes/${e.id}`, { version: e.version, codigo: e.codigo, nombre: e.nombre || null, activa: e.activa, atributos })
    else await api.post(`/productos/${props.producto.id}/variantes`, { codigo: e.codigo || null, nombre: e.nombre || null, activa: e.activa,
      atributos: Object.fromEntries(Object.entries(atributos).filter(([, v]) => v !== null)) })
    avisar(e.id ? 'Variante guardada.' : 'Variante creada.')
    editando.value = null
    emit('recargar')
  } catch (err) {
    errores.value = err.porCampo
    general.value = err
  } finally { guardando.value = false }
}

async function borrar(v) {
  const ok = await confirmar({ titulo: 'Borrar variante', mensaje: `Se borrará ${v.codigo} con sus identificadores y presentaciones propias.`, accion: 'Borrar', peligro: true })
  if (!ok) return
  try {
    await api.del(`/productos/${props.producto.id}/variantes/${v.id}`)
    avisar('Variante borrada.')
    emit('recargar')
  } catch (e) { avisarError(e) }
}

async function activar(v) {
  try {
    await api.patch(`/productos/${props.producto.id}/variantes/${v.id}`, { version: v.version, activa: !v.activa })
    emit('recargar')
  } catch (e) { avisarError(e) }
}

// ---- Generar combinaciones --------------------------------------------------------------
function abrirGenerar() {
  resultado.value = null
  generando.value = { ejes: Object.fromEntries(ejes.value.map((c) => [c.atributo.codigo, []])), texto: {} }
}
function alternar(codigo, valor) {
  const l = generando.value.ejes[codigo]
  const i = l.indexOf(valor)
  if (i >= 0) l.splice(i, 1)
  else l.push(valor)
}
function agregarTexto(c) {
  const t = (generando.value.texto[c.atributo.codigo] || '').trim()
  if (!t) return
  for (const parte of t.split(',').map((x) => x.trim()).filter(Boolean)) {
    const v = ['entero', 'decimal'].includes(c.atributo.tipo_dato) ? Number(parte) : parte
    if (!generando.value.ejes[c.atributo.codigo].includes(v)) generando.value.ejes[c.atributo.codigo].push(v)
  }
  generando.value.texto[c.atributo.codigo] = ''
}
const combinaciones = computed(() => generando.value ? Object.values(generando.value.ejes).reduce((n, l) => n * l.length, 1) : 0)

async function generar() {
  guardando.value = true
  try {
    resultado.value = await api.post(`/productos/${props.producto.id}/variantes/generar`, { ejes: generando.value.ejes })
    avisar(`${resultado.value.creadas.length} variantes creadas.`)
    emit('recargar')
  } catch (e) { avisarError(e) } finally { guardando.value = false }
}
const nombreOpcion = (c, v) => c.atributo.opciones?.find((o) => o.codigo === v)?.nombre ?? v
</script>

<template>
  <section class="tarjeta">
    <header class="tarjeta-cabeza">
      <div>
        <h2>Variantes</h2>
        <p>Se distinguen por {{ ejes.map((c) => c.atributo.nombre.toLowerCase()).join(' y ') || '—' }}. Cada combinación es un SKU.</p>
      </div>
      <div class="fila">
        <input v-if="producto.variantes.length > 8" v-model="busqueda" class="control buscar" type="search" placeholder="Buscar variante" aria-label="Buscar variante" />
        <button class="btn" type="button" :disabled="!ejes.length" @click="abrir()"><Icono nombre="mas" :tam="16" />Una variante</button>
        <button class="btn primario" type="button" :disabled="!ejes.length" @click="abrirGenerar"><Icono nombre="cuadricula" :tam="16" />Generar combinaciones</button>
      </div>
    </header>
    <div v-if="producto.variantes.length" class="tabla-envoltura">
      <table class="tabla">
        <thead><tr><th>SKU</th><th v-for="c in columnas" :key="c.atributo.id">{{ c.atributo.nombre }}</th><th>Nombre</th><th>Activa</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
        <tbody>
          <tr v-for="v in visibles" :key="v.id" :class="{ inactiva: !v.activa }">
            <td><code>{{ v.codigo }}</code></td>
            <td v-for="c in columnas" :key="c.atributo.id">
              <span v-if="c.es_eje" class="insignia sin-punto acento">{{ valorTexto(v.atributos[c.atributo.codigo], c.atributo) }}</span>
              <span v-else>{{ valorTexto(v.atributos[c.atributo.codigo], c.atributo) }}</span>
            </td>
            <td class="tenue">{{ v.nombre }}</td>
            <td><label class="interruptor"><input type="checkbox" :checked="v.activa" :aria-label="`Variante ${v.codigo} activa`" @change="activar(v)" /></label></td>
            <td class="acciones">
              <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${v.codigo}`" @click="abrir(v)"><Icono nombre="editar" :tam="16" /></button>
              <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Borrar ${v.codigo}`" @click="borrar(v)"><Icono nombre="borrar" :tam="16" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <EstadoVacio v-else-if="ejes.length" icono="cuadricula" titulo="Aún no hay variantes"
                 :texto="`Elija los valores de ${ejes.map((c) => c.atributo.nombre.toLowerCase()).join(' y ')} y se crean todas las combinaciones de una vez.`">
      <button class="btn primario" type="button" @click="abrirGenerar"><Icono nombre="cuadricula" :tam="16" />Generar combinaciones</button>
    </EstadoVacio>
    <EstadoVacio v-else icono="cuadricula" titulo="Este tipo no maneja variantes" texto="Para tener variantes, asigne al tipo un atributo de variante marcado como eje.">
      <RouterLink class="btn" :to="`/configuracion/tipos/${producto.tipo.id}`">Configurar el tipo</RouterLink>
    </EstadoVacio>
  </section>

  <Modal v-if="editando" :titulo="editando.id ? `Editar ${editando.codigo}` : 'Nueva variante'" ancho="560px" @cerrar="editando = null">
    <form id="form-variante" class="pila" novalidate @submit.prevent="guardar">
      <div v-if="general" class="aviso-caja error" role="alert">{{ general.message }}</div>
      <div class="rejilla-2">
        <CampoAtributo v-for="c in columnas" :key="c.atributo.id" v-model="editando.atributos[c.atributo.codigo]" :campo="c" :unidades="unidades"
                       :error="errores[`atributos.${c.atributo.codigo}`]" id-base="var" />
      </div>
      <div class="rejilla-2">
        <Campo etiqueta="SKU" id="v-codigo" :error="errores.codigo" :ayuda="editando.id ? '' : 'Vacío: se arma con la plantilla del tipo.'">
          <input id="v-codigo" v-model="editando.codigo" class="control mono" maxlength="80" :placeholder="editando.id ? '' : 'Automático'" />
        </Campo>
        <Campo etiqueta="Nombre" id="v-nombre" ayuda="Vacío: nombre del producto + valores de los ejes.">
          <input id="v-nombre" v-model="editando.nombre" class="control" maxlength="250" placeholder="Automático" />
        </Campo>
      </div>
      <label class="interruptor"><input v-model="editando.activa" type="checkbox" />Activa</label>
    </form>
    <template #pie>
      <button class="btn" type="button" @click="editando = null">Cancelar</button>
      <button class="btn primario" type="submit" form="form-variante" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar</button>
    </template>
  </Modal>

  <Modal v-if="generando" titulo="Generar combinaciones" descripcion="Elija los valores de cada eje. Las combinaciones que ya existen se omiten." ancho="640px" @cerrar="generando = null">
    <div v-if="!resultado" class="pila">
      <div v-for="c in ejes" :key="c.atributo.id" class="eje">
        <div class="fila entre"><h3>{{ c.atributo.nombre }}</h3>
          <button v-if="c.atributo.opciones?.length" class="btn fantasma chico" type="button"
                  @click="generando.ejes[c.atributo.codigo] = generando.ejes[c.atributo.codigo].length ? [] : c.atributo.opciones.filter((o) => o.activa).map((o) => o.codigo)">
            {{ generando.ejes[c.atributo.codigo].length ? 'Ninguno' : 'Todos' }}</button></div>
        <div v-if="c.atributo.tipo_dato === 'opcion'" class="valores" role="group" :aria-label="c.atributo.nombre">
          <button v-for="o in c.atributo.opciones.filter((o) => o.activa)" :key="o.codigo" type="button" class="valor"
                  :aria-pressed="generando.ejes[c.atributo.codigo].includes(o.codigo)" @click="alternar(c.atributo.codigo, o.codigo)">{{ o.nombre }}</button>
        </div>
        <div v-else-if="c.atributo.tipo_dato === 'booleano'" class="valores">
          <button v-for="b in [true, false]" :key="String(b)" type="button" class="valor" :aria-pressed="generando.ejes[c.atributo.codigo].includes(b)"
                  @click="alternar(c.atributo.codigo, b)">{{ b ? 'Sí' : 'No' }}</button>
        </div>
        <template v-else>
          <div class="fila">
            <input v-model="generando.texto[c.atributo.codigo]" class="control" :aria-label="`Valores de ${c.atributo.nombre}`"
                   placeholder="Escriba valores separados por coma y presione Enter" @keydown.enter.prevent="agregarTexto(c)" />
            <button class="btn" type="button" @click="agregarTexto(c)">Agregar</button>
          </div>
          <div class="valores">
            <span v-for="v in generando.ejes[c.atributo.codigo]" :key="String(v)" class="chip">{{ v }}
              <button type="button" :aria-label="`Quitar ${v}`" @click="alternar(c.atributo.codigo, v)"><Icono nombre="cerrar" :tam="12" /></button></span>
          </div>
        </template>
      </div>
      <div class="total" :class="{ listo: combinaciones }">
        <strong class="num">{{ combinaciones }}</strong> combinaciones
        <span v-if="combinaciones" class="tenue chico">· {{ ejes.map((c) => `${generando.ejes[c.atributo.codigo].length} ${c.atributo.nombre.toLowerCase()}`).join(' × ') }}</span>
      </div>
    </div>
    <div v-else class="pila">
      <div class="aviso-caja ok"><Icono nombre="check" /><span>Se crearon <strong>{{ resultado.creadas.length }}</strong> variantes.</span></div>
      <div v-if="resultado.omitidas.length" class="aviso-caja info"><Icono nombre="info" />
        <div>Se omitieron {{ resultado.omitidas.length }} porque ya existían:
          <ul><li v-for="(o, i) in resultado.omitidas.slice(0, 8)" :key="i">{{ Object.entries(o.valores).map(([k, v]) => nombreOpcion(ejes.find((c) => c.atributo.codigo === k), v)).join(' / ') }}</li></ul>
        </div>
      </div>
    </div>
    <template #pie>
      <template v-if="!resultado">
        <button class="btn" type="button" @click="generando = null">Cancelar</button>
        <button class="btn primario" type="button" :disabled="!combinaciones || guardando || combinaciones > 2000" @click="generar">
          <span v-if="guardando" class="cargando-btn" />Crear {{ combinaciones }} variantes</button>
      </template>
      <button v-else class="btn primario" type="button" @click="generando = null">Listo</button>
    </template>
  </Modal>
</template>

<style scoped>
.tarjeta { margin-top: var(--e-2); }
.buscar { width: 200px; }
tr.inactiva td:not(.acciones) { opacity: 0.55; }
.eje { display: flex; flex-direction: column; gap: var(--e-2); padding-bottom: var(--e-4); border-bottom: 1px solid var(--linea-suave); }
.valores { display: flex; flex-wrap: wrap; gap: 6px; }
.valor { min-width: 44px; height: 32px; padding: 0 12px; border-radius: var(--radio); border: 1px solid var(--borde-control); background: var(--superficie); color: var(--tinta-2); font: inherit; font-size: 13px; font-weight: 550; cursor: pointer; transition: all 0.12s; }
.valor:hover { border-color: var(--acento); }
.valor[aria-pressed='true'] { background: var(--acento); border-color: var(--acento); color: var(--sobre-acento); }
.total { padding: var(--e-3) var(--e-4); border-radius: var(--radio); background: var(--neutro-fondo); }
.total.listo { background: var(--acento-claro); color: var(--acento-texto); }
.total strong { font-size: 18px; }
</style>
