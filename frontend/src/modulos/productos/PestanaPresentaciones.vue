<script setup>
// Presentaciones: cómo se empaca o se comercia el producto (caja de 12, tambor de 250 kg…).
import { ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'

const props = defineProps({ producto: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const editando = ref(null)
const errores = ref({})
const guardando = ref(false)

function abrir(x = null) {
  errores.value = {}
  editando.value = x ? { ...x } : { codigo: '', nombre: '', unidad_id: props.unidades.find((u) => u.codigo === 'UN')?.id ?? null, cantidad: '', variante_id: null, activa: true }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  const { id, unidad: _u, ...cuerpo } = editando.value
  cuerpo.cantidad = cuerpo.cantidad === '' ? null : Number(cuerpo.cantidad)
  try {
    if (id) await api.patch(`/productos/${props.producto.id}/presentaciones/${id}`, cuerpo)
    else await api.post(`/productos/${props.producto.id}/presentaciones`, cuerpo)
    avisar('Presentación guardada.')
    editando.value = null
    emit('recargar')
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { guardando.value = false }
}

async function borrar(x) {
  if (!await confirmar({ titulo: 'Borrar presentación', mensaje: `Se borrará «${x.nombre}» y sus identificadores.`, accion: 'Borrar', peligro: true })) return
  try {
    await api.del(`/productos/${props.producto.id}/presentaciones/${x.id}`)
    avisar('Presentación borrada.')
    emit('recargar')
  } catch (e) { avisarError(e) }
}
const variante = (id) => props.producto.variantes.find((v) => v.id === id)?.codigo
</script>

<template>
  <section class="tarjeta">
    <header class="tarjeta-cabeza">
      <div><h2>Presentaciones</h2><p>Empaques y formas de venta, con su contenido en {{ producto.unidad.nombre.toLowerCase() }} ({{ producto.unidad.codigo }}).</p></div>
      <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Nueva presentación</button>
    </header>
    <div v-if="producto.presentaciones.length" class="tabla-envoltura">
      <table class="tabla">
        <thead><tr><th>Código</th><th>Nombre</th><th class="derecha">Contiene</th><th>Se cuenta en</th><th>Variante</th><th>Activa</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
        <tbody>
          <tr v-for="x in producto.presentaciones" :key="x.id">
            <td><code>{{ x.codigo }}</code></td>
            <td><strong class="peso">{{ x.nombre }}</strong></td>
            <td class="derecha num">{{ x.cantidad }} {{ producto.unidad.codigo }}</td>
            <td>{{ x.unidad }}</td>
            <td><code v-if="x.variante_id">{{ variante(x.variante_id) }}</code><span v-else class="tenue">Todas</span></td>
            <td><span class="insignia" :class="x.activa ? 'ok' : ''">{{ x.activa ? 'Sí' : 'No' }}</span></td>
            <td class="acciones">
              <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${x.nombre}`" @click="abrir(x)"><Icono nombre="editar" :tam="16" /></button>
              <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Borrar ${x.nombre}`" @click="borrar(x)"><Icono nombre="borrar" :tam="16" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <EstadoVacio v-else icono="caja" titulo="Sin presentaciones" texto="Agregue cómo se empaca o vende: caja de 12, bulto de 50 kg, tambor de 200 L…">
      <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Nueva presentación</button>
    </EstadoVacio>
  </section>

  <Modal v-if="editando" :titulo="editando.id ? 'Editar presentación' : 'Nueva presentación'" @cerrar="editando = null">
    <form id="form-pres" class="pila" @submit.prevent="guardar">
      <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
      <div class="rejilla-2">
        <Campo etiqueta="Nombre" id="pr-nombre" :error="errores.nombre" obligatorio><input id="pr-nombre" v-model="editando.nombre" class="control" required maxlength="100" placeholder="Caja de 12" /></Campo>
        <Campo etiqueta="Código" id="pr-codigo" :error="errores.codigo" obligatorio><input id="pr-codigo" v-model="editando.codigo" class="control mono" required maxlength="40" placeholder="CJ12" /></Campo>
        <Campo etiqueta="Contiene" id="pr-cant" :error="errores.cantidad" obligatorio :ayuda="`Cantidad en ${producto.unidad.nombre.toLowerCase()} (${producto.unidad.codigo}).`">
          <input id="pr-cant" v-model="editando.cantidad" class="control num" type="number" step="any" min="0" required /></Campo>
        <Campo etiqueta="Se cuenta en" id="pr-unidad" :error="errores.unidad_id" obligatorio ayuda="La unidad de la presentación misma (caja, tambor…).">
          <select id="pr-unidad" v-model="editando.unidad_id" class="control" required>
            <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
          </select></Campo>
      </div>
      <Campo v-if="producto.variantes.length" etiqueta="Solo para la variante" id="pr-var" :error="errores.variante_id">
        <select id="pr-var" v-model="editando.variante_id" class="control">
          <option :value="null">Todas las variantes</option>
          <option v-for="v in producto.variantes" :key="v.id" :value="v.id">{{ v.codigo }}</option>
        </select></Campo>
      <label class="interruptor"><input v-model="editando.activa" type="checkbox" />Activa</label>
    </form>
    <template #pie>
      <button class="btn" type="button" @click="editando = null">Cancelar</button>
      <button class="btn primario" type="submit" form="form-pres" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar</button>
    </template>
  </Modal>
</template>

<style scoped>
.tarjeta { margin-top: var(--e-2); }
.peso { font-weight: 550; }
</style>
