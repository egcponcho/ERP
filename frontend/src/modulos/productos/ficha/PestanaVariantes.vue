<script setup>
// Variantes en la tabla común: cada fila se abre para editarla en el mismo lugar;
// «Agregar variantes» abre el generador de combinaciones dentro de la página.
import { computed, reactive, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { valorTexto } from '@/nucleo/formato.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ producto: { type: Object, required: true }, esquema: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const ejes = computed(() => props.esquema.campos.filter((c) => c.es_eje))
const otros = computed(() => props.esquema.campos.filter((c) => c.nivel === 'variante' && !c.es_eje))
const columnas = computed(() => [
  { clave: 'codigo', texto: 'SKU', fija: true, prioridad: 1 },
  ...ejes.value.map((c) => ({ clave: `a_${c.atributo.codigo}`, texto: c.atributo.nombre, prioridad: 1, valor: (f) => valorTexto(f.atributos[c.atributo.codigo], c.atributo) })),
  ...otros.value.map((c) => ({ clave: `a_${c.atributo.codigo}`, texto: c.atributo.nombre, prioridad: 3, valor: (f) => valorTexto(f.atributos[c.atributo.codigo], c.atributo) })),
  { clave: 'nombre', texto: 'Nombre', prioridad: 3, filtro: false },
  { clave: 'activa', texto: 'Activa', prioridad: 2, valor: (f) => f.activa, textoValor: (v) => (v ? 'Sí' : 'No') },
])

// ---- Editar una variante (en su fila) ---------------------------------------------------
const edicion = reactive({}) // id → { codigo, nombre, atributos, errores }
function abrir(v) {
  edicion[v.id] = { codigo: v.codigo, nombre: v.nombre, atributos: JSON.parse(JSON.stringify(v.atributos)), errores: {} }
}
async function guardar(v) {
  const e = edicion[v.id]
  e.errores = {}
  const atributos = Object.fromEntries([...ejes.value, ...otros.value].map((c) => {
    const x = e.atributos[c.atributo.codigo]
    return [c.atributo.codigo, x === '' || (Array.isArray(x) && !x.length) ? null : x ?? null]
  }))
  try {
    await api.patch(`/productos/${props.producto.id}/variantes/${v.id}`, { version: v.version, codigo: e.codigo, nombre: e.nombre || null, atributos })
    avisar(`Variante ${e.codigo} guardada.`)
    emit('recargar')
  } catch (err) {
    e.errores = { ...err.porCampo, _general: err.message }
  }
}
async function activar(v) {
  try {
    await api.patch(`/productos/${props.producto.id}/variantes/${v.id}`, { version: v.version, activa: !v.activa })
    emit('recargar')
  } catch (e) { avisarError(e) }
}
async function borrar(v) {
  try {
    await api.del(`/productos/${props.producto.id}/variantes/${v.id}`)
    avisar(`Se borró ${v.codigo}.`)
    emit('recargar')
  } catch (e) { avisarError(e) }
}

// ---- Generar combinaciones ----------------------------------------------------------------
const generando = ref(null) // { ejes: {codigo: []}, texto: {} }
const resultado = ref(null)
function abrirGenerador() {
  resultado.value = null
  generando.value = { ejes: Object.fromEntries(ejes.value.map((c) => [c.atributo.codigo, []])), texto: {} }
}
function alternar(codigo, v) {
  const l = generando.value.ejes[codigo]
  const i = l.indexOf(v)
  if (i >= 0) l.splice(i, 1)
  else l.push(v)
}
function agregarTexto(c) {
  const t = (generando.value.texto[c.atributo.codigo] || '').trim()
  for (const parte of t.split(',').map((x) => x.trim()).filter(Boolean)) {
    const v = ['entero', 'decimal'].includes(c.atributo.tipo_dato) ? Number(parte) : parte
    if (!generando.value.ejes[c.atributo.codigo].includes(v)) generando.value.ejes[c.atributo.codigo].push(v)
  }
  generando.value.texto[c.atributo.codigo] = ''
}
const total = computed(() => (generando.value ? Object.values(generando.value.ejes).reduce((n, l) => n * l.length, 1) : 0))
async function generar() {
  try {
    resultado.value = await api.post(`/productos/${props.producto.id}/variantes/generar`, { ejes: generando.value.ejes })
    avisar(`${resultado.value.creadas.length} variantes creadas${resultado.value.omitidas.length ? `; ${resultado.value.omitidas.length} ya existían` : ''}.`)
    generando.value = null
    emit('recargar')
  } catch (e) { avisarError(e) }
}
const nombreOpcion = (c, v) => c.atributo.opciones?.find((o) => o.codigo === v)?.nombre ?? String(v)
</script>

<template>
  <div>
    <div class="fila-flex mb-3">
      <p class="ayuda crece">Se distinguen por {{ ejes.map((c) => c.atributo.nombre.toLowerCase()).join(' y ') || '—' }}. Abra una fila para editarla.</p>
      <button v-if="ejes.length && !generando" type="button" class="btn btn-primario" @click="abrirGenerador"><Icono nombre="mas" :tam="16" />Agregar variantes</button>
    </div>

    <PanelEnLinea v-if="generando" titulo="Agregar variantes" descripcion="Elija los valores; se crean todas las combinaciones y se omiten las que ya existen." @cerrar="generando = null">
      <div v-for="c in ejes" :key="c.atributo.id" class="eje">
        <p class="resumen-titulo">{{ c.atributo.nombre }} · {{ generando.ejes[c.atributo.codigo].length }}</p>
        <div v-if="c.atributo.tipo_dato === 'opcion'" class="opciones-chips">
          <button v-for="o in c.atributo.opciones.filter((x) => x.activa)" :key="o.codigo" type="button" class="opcion-chip"
                  :aria-pressed="generando.ejes[c.atributo.codigo].includes(o.codigo)" @click="alternar(c.atributo.codigo, o.codigo)">{{ o.nombre }}</button>
        </div>
        <div v-else class="fila-flex">
          <input v-model="generando.texto[c.atributo.codigo]" class="entrada crece" placeholder="Valores separados por coma" :aria-label="`Valores de ${c.atributo.nombre}`" @keydown.enter.prevent="agregarTexto(c)" />
          <button type="button" class="btn" @click="agregarTexto(c)">Agregar</button>
          <span v-for="v in generando.ejes[c.atributo.codigo]" :key="String(v)" class="chip">{{ v }}
            <button type="button" :aria-label="`Quitar ${v}`" @click="alternar(c.atributo.codigo, v)"><Icono nombre="cerrar" :tam="12" /></button></span>
        </div>
      </div>
      <template #pie>
        <span class="ayuda separar">{{ total }} combinaciones</span>
        <button type="button" class="btn" @click="generando = null">Cancelar</button>
        <button type="button" class="btn btn-primario" :disabled="!total || total > 2000" @click="generar">Crear {{ total }} variantes</button>
      </template>
    </PanelEnLinea>

    <TablaDatos tabla="variantes" :columnas="columnas" :filas="producto.variantes" expandible etiqueta="Variantes" orden-inicial="codigo:asc"
                :clase-fila="(f) => ({ apagado: !f.activa })" @expandir="abrir">
      <template #celda-codigo="{ fila }"><strong class="codigo">{{ fila.codigo }}</strong></template>
      <template v-for="c in ejes" :key="c.atributo.id" #[`celda-a_${c.atributo.codigo}`]="{ fila }">
        <span class="etiqueta acento ms-0">{{ valorTexto(fila.atributos[c.atributo.codigo], c.atributo) }}</span></template>
      <template v-for="c in otros" :key="c.atributo.id" #[`celda-a_${c.atributo.codigo}`]="{ fila }">{{ valorTexto(fila.atributos[c.atributo.codigo], c.atributo) }}</template>
      <template #celda-activa="{ fila }"><label class="check" @click.stop><input type="checkbox" :checked="fila.activa" :aria-label="`${fila.codigo} activa`" @change="activar(fila)" /></label></template>
      <template #acciones="{ fila }"><BotonConfirmar :etiqueta="`Borrar ${fila.codigo}`" @confirmar="borrar(fila)" /></template>
      <template #detalle="{ fila }">
        <form v-if="edicion[fila.id]" class="edicion" @submit.prevent="guardar(fila)">
          <p v-if="edicion[fila.id].errores._general" class="nota error">{{ edicion[fila.id].errores._general }}</p>
          <div class="rejilla-campos">
            <CampoAtributo v-for="c in [...ejes, ...otros]" :key="c.atributo.id" v-model="edicion[fila.id].atributos[c.atributo.codigo]" :campo="c"
                           :unidades="unidades" :error="edicion[fila.id].errores[`atributos.${c.atributo.codigo}`]" :id-base="`v${fila.id}`" />
            <label class="campo"><span class="req">SKU</span><input v-model="edicion[fila.id].codigo" class="entrada mono" maxlength="80" /></label>
            <label class="campo"><span>Nombre</span><input v-model="edicion[fila.id].nombre" class="entrada" maxlength="250" /></label>
          </div>
          <div class="fila-flex mt-chico"><button type="submit" class="btn btn-primario btn-chico"><Icono nombre="check" :tam="14" />Guardar variante</button></div>
        </form>
      </template>
      <template #vacio>
        <span v-if="ejes.length">Todavía no hay variantes. <button type="button" class="btn-texto" @click="abrirGenerador">Agregar variantes</button></span>
        <span v-else>Este tipo no maneja variantes. <RouterLink :to="`/productos/configuracion/tipos/${producto.tipo.id}`">Configurar el tipo</RouterLink></span>
      </template>
    </TablaDatos>
    <p v-if="resultado?.omitidas.length" class="ayuda mt-chico">Ya existían: {{ resultado.omitidas.map((o) => Object.entries(o.valores).map(([k, v]) => nombreOpcion(ejes.find((c) => c.atributo.codigo === k), v)).join(' / ')).join(', ') }}</p>
  </div>
</template>

<style scoped>
.eje + .eje { margin-top: 12px; }
.edicion { display: flex; flex-direction: column; gap: 10px; }
</style>
