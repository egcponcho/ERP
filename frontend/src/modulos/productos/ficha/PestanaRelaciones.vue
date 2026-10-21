<script setup>
// Relaciones con otros productos (componentes, sustitutos, accesorios…) y dónde se usa este.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import CeldaEditable from '@/componentes/CeldaEditable.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import SelectorProducto from '@/componentes/SelectorProducto.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ producto: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const tipos = ref([])
const usadoEn = ref([])
const nueva = ref(null)
const error = ref('')

onMounted(async () => {
  try { ;[tipos.value, usadoEn.value] = await Promise.all([catalogo('tipos-relacion', { recargar: true }), api.get(`/productos/${props.producto.id}/usado-en`)]) }
  catch (e) { avisarError(e) }
})
const tipo = computed(() => tipos.value.find((t) => t.id === nueva.value?.tipo_id))
const COLUMNAS = [
  { clave: 'tipo', texto: 'Relación', valor: (f) => tipos.value.find((t) => t.id === f.tipo_id)?.nombre || f.tipo },
  { clave: 'destino', texto: 'Producto', fija: true, valor: (f) => `${f.destino.codigo} · ${f.destino.nombre}` },
  { clave: 'cantidad', texto: 'Cantidad', num: true, filtro: false },
]
const COLUMNAS_USO = [
  { clave: 'nombre', texto: 'Relación' },
  { clave: 'origen', texto: 'Producto', fija: true, valor: (f) => `${f.origen.codigo} · ${f.origen.nombre}` },
  { clave: 'cantidad', texto: 'Cantidad', num: true, filtro: false },
]

function abrir() {
  error.value = ''
  nueva.value = { tipo_id: tipos.value.find((t) => t.activo)?.id ?? null, destino_id: null, cantidad: '', unidad_id: null }
}
async function crear() {
  error.value = ''
  const n = nueva.value
  try {
    await api.post(`/productos/${props.producto.id}/relaciones`, { tipo_id: n.tipo_id, destino_id: n.destino_id,
      cantidad: tipo.value?.con_cantidad && n.cantidad !== '' ? Number(n.cantidad) : null, unidad_id: tipo.value?.con_cantidad ? n.unidad_id : null })
    avisar('Relación agregada.')
    nueva.value = null
    emit('recargar')
  } catch (e) { error.value = e.message }
}
async function cambiarCantidad(r, v) {
  try { await api.patch(`/productos/${props.producto.id}/relaciones/${r.id}`, { cantidad: v }); emit('recargar') } catch (e) { avisarError(e); throw e }
}
async function borrar(r) {
  try {
    await api.del(`/productos/${props.producto.id}/relaciones/${r.id}`)
    avisar('Relación quitada.')
    emit('recargar')
  } catch (e) { avisarError(e) }
}
const conCantidad = (f) => tipos.value.find((t) => t.id === f.tipo_id)?.con_cantidad
</script>

<template>
  <div>
    <div class="fila-flex mb-3">
      <p class="ayuda crece">Listas de materiales, kits, sustitutos y accesorios. Un producto no puede contenerse a sí mismo, ni de forma indirecta.</p>
      <button v-if="!nueva" type="button" class="btn btn-primario" :disabled="!tipos.length" @click="abrir"><Icono nombre="mas" :tam="16" />Relacionar producto</button>
    </div>
    <PanelEnLinea v-if="nueva" titulo="Relacionar producto" @cerrar="nueva = null">
      <p v-if="error" class="nota error mb-3">{{ error }}</p>
      <div class="rejilla-campos">
        <label class="campo"><span class="req">Relación</span>
          <select v-model="nueva.tipo_id" class="entrada"><option v-for="t in tipos.filter((x) => x.activo)" :key="t.id" :value="t.id">{{ t.nombre }}</option></select></label>
        <div class="campo col-2"><label for="rel-destino"><span class="req">Producto</span></label>
          <SelectorProducto id="rel-destino" v-model="nueva.destino_id" :excluir="producto.id" /></div>
        <template v-if="tipo?.con_cantidad">
          <label class="campo"><span class="req">Cantidad</span><input v-model="nueva.cantidad" class="entrada num" type="number" min="0" step="any" /></label>
          <label class="campo"><span>Unidad</span><select v-model="nueva.unidad_id" class="entrada"><option :value="null">La del producto</option>
            <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }}</option></select></label>
        </template>
      </div>
      <template #pie>
        <button type="button" class="btn" @click="nueva = null">Cancelar</button>
        <button type="button" class="btn btn-primario" :disabled="!nueva.destino_id" @click="crear"><Icono nombre="check" :tam="16" />Agregar</button>
      </template>
    </PanelEnLinea>
    <TablaDatos tabla="relaciones" :columnas="COLUMNAS" :filas="producto.relaciones" etiqueta="Relaciones">
      <template #celda-tipo="{ fila }">{{ tipos.find((t) => t.id === fila.tipo_id)?.nombre || fila.tipo }}</template>
      <template #celda-destino="{ fila }"><RouterLink :to="`/productos/${fila.destino.id}`"><code>{{ fila.destino.codigo }}</code> · {{ fila.destino.nombre }}</RouterLink></template>
      <template #celda-cantidad="{ fila }">
        <CeldaEditable v-if="conCantidad(fila)" :valor="fila.cantidad" tipo="number" etiqueta="Cantidad" ancho="100px" :guardar="(v) => cambiarCantidad(fila, v)" />
        <span v-else class="apagado">—</span><span v-if="fila.unidad" class="sub">{{ fila.unidad }}</span></template>
      <template #acciones="{ fila }"><BotonConfirmar :etiqueta="`Quitar relación con ${fila.destino.nombre}`" pregunta="¿Quitar?" confirmar="Sí, quitar" @confirmar="borrar(fila)" /></template>
      <template #vacio>Sin relaciones con otros productos.</template>
    </TablaDatos>

    <h2 class="mt mb-3">Dónde se usa</h2>
    <TablaDatos tabla="usado-en" :columnas="COLUMNAS_USO" :filas="usadoEn" etiqueta="Dónde se usa">
      <template #celda-origen="{ fila }"><RouterLink :to="`/productos/${fila.origen.id}`"><code>{{ fila.origen.codigo }}</code> · {{ fila.origen.nombre }}</RouterLink></template>
      <template #celda-cantidad="{ fila }">{{ fila.cantidad ?? '—' }}</template>
      <template #vacio>Ningún otro producto usa este.</template>
    </TablaDatos>
  </div>
</template>
