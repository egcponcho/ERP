<script setup>
// Códigos de barras y códigos alternos del producto, de una variante o de una presentación.
import { onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ producto: { type: Object, required: true } })
const emit = defineEmits(['recargar'])
const tipos = ref([])
const nuevo = ref(null)
const error = ref('')
onMounted(async () => { tipos.value = (await catalogo('tipos-identificador', { recargar: true })).filter((t) => t.activo) })

const aplica = (x) => (x.variante_id ? `Variante ${props.producto.variantes.find((v) => v.id === x.variante_id)?.codigo}`
  : x.presentacion_id ? `Presentación ${props.producto.presentaciones.find((p) => p.id === x.presentacion_id)?.nombre}` : 'Producto')
const COLUMNAS = [
  { clave: 'tipo', texto: 'Tipo', valor: (f) => tipos.value.find((t) => t.codigo === f.tipo)?.nombre || f.tipo },
  { clave: 'valor', texto: 'Código', fija: true, filtro: false },
  { clave: 'aplica', texto: 'Es de', valor: aplica },
]

function abrir() {
  error.value = ''
  nuevo.value = { tipo_id: tipos.value[0]?.id ?? null, valor: '', destino: '' }
}
async function crear() {
  error.value = ''
  const [clase, id] = nuevo.value.destino.split(':')
  try {
    await api.post(`/productos/${props.producto.id}/identificadores`, { tipo_id: nuevo.value.tipo_id, valor: nuevo.value.valor,
      variante_id: clase === 'v' ? Number(id) : null, presentacion_id: clase === 'p' ? Number(id) : null })
    avisar('Código agregado.')
    nuevo.value = null
    emit('recargar')
  } catch (e) { error.value = e.message }
}
async function borrar(x) {
  try {
    await api.del(`/productos/${props.producto.id}/identificadores/${x.id}`)
    avisar(`Se quitó ${x.valor}.`)
    emit('recargar')
  } catch (e) { avisarError(e) }
}
async function copiar(v) {
  try { await navigator.clipboard.writeText(v); avisar('Copiado.', 'info', 1500) } catch { /* sin portapapeles */ }
}
const patron = (id) => tipos.value.find((t) => t.id === id)?.patron
</script>

<template>
  <div>
    <div class="fila-flex mb-3">
      <p class="ayuda crece">Un mismo código no se repite en ningún otro producto de su tipo.</p>
      <button v-if="!nuevo" type="button" class="btn btn-primario" :disabled="!tipos.length" @click="abrir"><Icono nombre="mas" :tam="16" />Agregar código</button>
    </div>
    <PanelEnLinea v-if="nuevo" titulo="Nuevo código" @cerrar="nuevo = null">
      <p v-if="error" class="nota error mb-3">{{ error }}</p>
      <div class="rejilla-campos">
        <label class="campo"><span class="req">Tipo</span><select v-model="nuevo.tipo_id" class="entrada"><option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option></select></label>
        <label class="campo"><span class="req">Código</span><input v-model="nuevo.valor" class="entrada mono" maxlength="100" :placeholder="patron(nuevo.tipo_id) ? `Formato ${patron(nuevo.tipo_id)}` : ''" autofocus @keydown.enter="crear" /></label>
        <label class="campo"><span>Es de</span>
          <select v-model="nuevo.destino" class="entrada">
            <option value="">El producto</option>
            <optgroup v-if="producto.variantes.length" label="Variantes"><option v-for="v in producto.variantes" :key="v.id" :value="`v:${v.id}`">{{ v.codigo }}</option></optgroup>
            <optgroup v-if="producto.presentaciones.length" label="Presentaciones"><option v-for="p in producto.presentaciones" :key="p.id" :value="`p:${p.id}`">{{ p.nombre }}</option></optgroup>
          </select></label>
      </div>
      <template #pie>
        <button type="button" class="btn" @click="nuevo = null">Cancelar</button>
        <button type="button" class="btn btn-primario" :disabled="!nuevo.valor.trim()" @click="crear"><Icono nombre="check" :tam="16" />Agregar</button>
      </template>
    </PanelEnLinea>
    <TablaDatos tabla="identificadores" :columnas="COLUMNAS" :filas="producto.identificadores" etiqueta="Códigos">
      <template #celda-tipo="{ fila }">{{ tipos.find((t) => t.codigo === fila.tipo)?.nombre || fila.tipo }}</template>
      <template #celda-valor="{ fila }"><button type="button" class="enlace-codigo" title="Copiar" @click="copiar(fila.valor)"><code>{{ fila.valor }}</code></button></template>
      <template #celda-aplica="{ fila }">{{ aplica(fila) }}</template>
      <template #acciones="{ fila }"><BotonConfirmar :etiqueta="`Quitar ${fila.valor}`" pregunta="¿Quitar?" confirmar="Sí, quitar" @confirmar="borrar(fila)" /></template>
      <template #vacio>Sin códigos. Agregue el EAN, UPC o el código del proveedor para encontrar el producto al escanearlo.</template>
    </TablaDatos>
  </div>
</template>

<style scoped>
.enlace-codigo { border: 0; background: none; padding: 2px 4px; margin-inline-start: -4px; border-radius: 4px; cursor: copy; color: inherit; font: inherit; }
.enlace-codigo:hover { background: var(--linea-suave); }
</style>
