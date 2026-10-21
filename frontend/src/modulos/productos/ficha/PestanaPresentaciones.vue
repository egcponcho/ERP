<script setup>
// Presentaciones en la tabla común: nombre y contenido se corrigen en la misma celda.
import { reactive, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import CeldaEditable from '@/componentes/CeldaEditable.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ producto: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const nueva = ref(null)
const errores = ref({})
const COLUMNAS = [
  { clave: 'codigo', texto: 'Código', fija: true },
  { clave: 'nombre', texto: 'Nombre', filtro: false },
  { clave: 'cantidad', texto: 'Contiene', num: true, filtro: false },
  { clave: 'unidad', texto: 'Se cuenta en' },
  { clave: 'variante', texto: 'Variante', valor: (f) => props.producto.variantes.find((v) => v.id === f.variante_id)?.codigo || 'Todas' },
  { clave: 'activa', texto: 'Activa', valor: (f) => f.activa, textoValor: (v) => (v ? 'Sí' : 'No') },
]

function abrir() {
  errores.value = {}
  nueva.value = reactive({ nombre: '', codigo: '', cantidad: '', unidad_id: props.unidades.find((u) => u.codigo === 'UN')?.id ?? null, variante_id: null })
}
async function crear() {
  errores.value = {}
  try {
    await api.post(`/productos/${props.producto.id}/presentaciones`, { ...nueva.value, cantidad: nueva.value.cantidad === '' ? null : Number(nueva.value.cantidad) })
    avisar('Presentación agregada.')
    nueva.value = null
    emit('recargar')
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } }
}
async function cambiar(x, campo, valor) {
  try {
    await api.patch(`/productos/${props.producto.id}/presentaciones/${x.id}`, { [campo]: valor })
    emit('recargar')
  } catch (e) { avisarError(e); throw e }
}
async function borrar(x) {
  try {
    await api.del(`/productos/${props.producto.id}/presentaciones/${x.id}`)
    avisar(`Se borró ${x.nombre}.`)
    emit('recargar')
  } catch (e) { avisarError(e) }
}
</script>

<template>
  <div>
    <div class="fila-flex mb-3">
      <p class="ayuda crece">Cómo se empaca o se vende, con su contenido en {{ producto.unidad.nombre.toLowerCase() }} ({{ producto.unidad.codigo }}).</p>
      <button v-if="!nueva" type="button" class="btn btn-primario" @click="abrir"><Icono nombre="mas" :tam="16" />Agregar presentación</button>
    </div>
    <PanelEnLinea v-if="nueva" titulo="Nueva presentación" @cerrar="nueva = null">
      <p v-if="errores._general" class="nota error mb-3">{{ errores._general }}</p>
      <div class="rejilla-campos">
        <label class="campo" :class="{ 'con-error': errores.nombre }"><span class="req">Nombre</span><input v-model="nueva.nombre" class="entrada" placeholder="Caja de 12" autofocus /></label>
        <label class="campo" :class="{ 'con-error': errores.codigo }"><span class="req">Código</span><input v-model="nueva.codigo" class="entrada mono" maxlength="40" placeholder="CJ12" /></label>
        <label class="campo" :class="{ 'con-error': errores.cantidad }"><span class="req">Contiene ({{ producto.unidad.codigo }})</span><input v-model="nueva.cantidad" class="entrada num" type="number" min="0" step="any" /></label>
        <label class="campo"><span>Se cuenta en</span><select v-model="nueva.unidad_id" class="entrada"><option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }}</option></select></label>
        <label v-if="producto.variantes.length" class="campo"><span>Solo para la variante</span>
          <select v-model="nueva.variante_id" class="entrada"><option :value="null">Todas</option><option v-for="v in producto.variantes" :key="v.id" :value="v.id">{{ v.codigo }}</option></select></label>
      </div>
      <template #pie>
        <button type="button" class="btn" @click="nueva = null">Cancelar</button>
        <button type="button" class="btn btn-primario" @click="crear"><Icono nombre="check" :tam="16" />Agregar</button>
      </template>
    </PanelEnLinea>
    <TablaDatos tabla="presentaciones" :columnas="COLUMNAS" :filas="producto.presentaciones" etiqueta="Presentaciones" orden-inicial="cantidad:asc">
      <template #celda-codigo="{ fila }"><strong class="codigo">{{ fila.codigo }}</strong></template>
      <template #celda-nombre="{ fila }"><CeldaEditable :valor="fila.nombre" etiqueta="Nombre" :guardar="(v) => cambiar(fila, 'nombre', v)" /></template>
      <template #celda-cantidad="{ fila }"><CeldaEditable :valor="fila.cantidad" tipo="number" etiqueta="Contiene" ancho="110px" :guardar="(v) => cambiar(fila, 'cantidad', v)" /></template>
      <template #celda-variante="{ fila }"><code v-if="fila.variante_id">{{ producto.variantes.find((v) => v.id === fila.variante_id)?.codigo }}</code><span v-else class="apagado">Todas</span></template>
      <template #celda-activa="{ fila }"><label class="check"><input type="checkbox" :checked="fila.activa" :aria-label="`${fila.nombre} activa`" @change="cambiar(fila, 'activa', !fila.activa)" /></label></template>
      <template #acciones="{ fila }"><BotonConfirmar :etiqueta="`Borrar ${fila.nombre}`" @confirmar="borrar(fila)" /></template>
      <template #vacio>Sin presentaciones: el producto se maneja solo en {{ producto.unidad.nombre.toLowerCase() }}. <button type="button" class="btn-texto" @click="abrir">Agregar la primera</button></template>
    </TablaDatos>
  </div>
</template>
