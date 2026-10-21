<script setup>
// Identificadores: códigos alternos (EAN, UPC, código del proveedor…) del producto,
// de una variante o de una presentación.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'

const props = defineProps({ producto: { type: Object, required: true } })
const emit = defineEmits(['recargar'])
const tipos = ref([])
const nuevo = ref(null)
const errores = ref({})
const guardando = ref(false)

onMounted(async () => { tipos.value = (await catalogo('tipos-identificador', { recargar: true })).filter((t) => t.activo) })
const tipo = computed(() => tipos.value.find((t) => t.id === nuevo.value?.tipo_id))

function abrir() {
  errores.value = {}
  nuevo.value = { tipo_id: tipos.value[0]?.id ?? null, valor: '', aplica: 'producto', variante_id: null, presentacion_id: null }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  const n = nuevo.value
  try {
    await api.post(`/productos/${props.producto.id}/identificadores`, { tipo_id: n.tipo_id, valor: n.valor,
      variante_id: n.aplica === 'variante' ? n.variante_id : null, presentacion_id: n.aplica === 'presentacion' ? n.presentacion_id : null })
    avisar('Identificador agregado.')
    nuevo.value = null
    emit('recargar')
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { guardando.value = false }
}

async function borrar(x) {
  if (!await confirmar({ titulo: 'Quitar identificador', mensaje: `Se quitará ${x.tipo} ${x.valor}.`, accion: 'Quitar', peligro: true })) return
  try {
    await api.del(`/productos/${props.producto.id}/identificadores/${x.id}`)
    avisar('Identificador quitado.')
    emit('recargar')
  } catch (e) { avisarError(e) }
}

async function copiar(valor) {
  try { await navigator.clipboard.writeText(valor); avisar('Copiado al portapapeles.', 'info', 1800) } catch { /* sin portapapeles */ }
}
const nombreTipo = (codigo) => tipos.value.find((t) => t.codigo === codigo)?.nombre || codigo
const aplica = (x) => x.variante_id ? `Variante ${props.producto.variantes.find((v) => v.id === x.variante_id)?.codigo}`
  : x.presentacion_id ? `Presentación ${props.producto.presentaciones.find((p) => p.id === x.presentacion_id)?.nombre}` : 'Producto'
</script>

<template>
  <section class="tarjeta">
    <header class="tarjeta-cabeza">
      <div><h2>Identificadores</h2><p>Códigos de barras y códigos alternos. Un mismo código no se repite en ningún otro producto.</p></div>
      <button class="btn primario" type="button" :disabled="!tipos.length" @click="abrir"><Icono nombre="mas" :tam="16" />Agregar código</button>
    </header>
    <div v-if="producto.identificadores.length" class="tabla-envoltura">
      <table class="tabla">
        <thead><tr><th>Tipo</th><th>Código</th><th>Aplica a</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
        <tbody>
          <tr v-for="x in producto.identificadores" :key="x.id">
            <td>{{ nombreTipo(x.tipo) }}</td>
            <td><button class="codigo" type="button" title="Copiar" @click="copiar(x.valor)"><code>{{ x.valor }}</code></button></td>
            <td class="tenue">{{ aplica(x) }}</td>
            <td class="acciones"><button class="btn fantasma icono chico peligro" type="button" :aria-label="`Quitar ${x.valor}`" @click="borrar(x)"><Icono nombre="borrar" :tam="16" /></button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <EstadoVacio v-else icono="codigo" titulo="Sin identificadores" :texto="tipos.length ? 'Agregue el EAN, UPC o el código del proveedor para encontrar el producto al escanearlo.' : 'Primero configure los tipos de identificador.'">
      <button v-if="tipos.length" class="btn primario" type="button" @click="abrir"><Icono nombre="mas" :tam="16" />Agregar código</button>
      <RouterLink v-else class="btn" to="/configuracion/tipos-identificador">Configurar</RouterLink>
    </EstadoVacio>
  </section>

  <Modal v-if="nuevo" titulo="Agregar identificador" @cerrar="nuevo = null">
    <form id="form-ident" class="pila" @submit.prevent="guardar">
      <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
      <div class="rejilla-2">
        <Campo etiqueta="Tipo" id="i-tipo" obligatorio>
          <select id="i-tipo" v-model="nuevo.tipo_id" class="control" required>
            <option v-for="t in tipos" :key="t.id" :value="t.id">{{ t.nombre }}</option>
          </select></Campo>
        <Campo etiqueta="Código" id="i-valor" :error="errores.valor" obligatorio :ayuda="tipo?.patron ? `Formato: ${tipo.patron}` : ''">
          <input id="i-valor" v-model="nuevo.valor" class="control mono" required maxlength="100" autofocus /></Campo>
      </div>
      <fieldset class="aplica">
        <legend class="etiqueta">Aplica a</legend>
        <label class="interruptor"><input v-model="nuevo.aplica" type="radio" value="producto" />El producto</label>
        <label v-if="producto.variantes.length" class="interruptor"><input v-model="nuevo.aplica" type="radio" value="variante" />Una variante</label>
        <label v-if="producto.presentaciones.length" class="interruptor"><input v-model="nuevo.aplica" type="radio" value="presentacion" />Una presentación</label>
      </fieldset>
      <select v-if="nuevo.aplica === 'variante'" v-model="nuevo.variante_id" class="control" aria-label="Variante" required>
        <option :value="null" disabled>Elegir variante…</option>
        <option v-for="v in producto.variantes" :key="v.id" :value="v.id">{{ v.codigo }} · {{ v.nombre }}</option>
      </select>
      <select v-if="nuevo.aplica === 'presentacion'" v-model="nuevo.presentacion_id" class="control" aria-label="Presentación" required>
        <option :value="null" disabled>Elegir presentación…</option>
        <option v-for="p in producto.presentaciones" :key="p.id" :value="p.id">{{ p.nombre }}</option>
      </select>
    </form>
    <template #pie>
      <button class="btn" type="button" @click="nuevo = null">Cancelar</button>
      <button class="btn primario" type="submit" form="form-ident" :disabled="guardando || !nuevo.valor.trim()"><span v-if="guardando" class="cargando-btn" />Agregar</button>
    </template>
  </Modal>
</template>

<style scoped>
.tarjeta { margin-top: var(--e-2); }
.codigo { border: 0; background: transparent; padding: 2px 4px; margin-left: -4px; border-radius: 4px; cursor: copy; color: inherit; }
.codigo:hover { background: var(--neutro-fondo); }
.aplica { border: 0; margin: 0; padding: 0; display: flex; gap: var(--e-5); flex-wrap: wrap; }
.aplica legend { margin-bottom: var(--e-2); }
.aplica input[type='radio'] { width: 16px; height: 16px; border-radius: 50%; appearance: auto; accent-color: var(--acento); }
.aplica input[type='radio']::after { display: none; }
</style>
