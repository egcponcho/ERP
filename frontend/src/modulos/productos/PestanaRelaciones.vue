<script setup>
// Relaciones con otros productos (componentes, sustitutos, accesorios…) y dónde se usa este.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import SelectorProducto from '@/componentes/SelectorProducto.vue'

const props = defineProps({ producto: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['recargar'])
const tipos = ref([])
const usadoEn = ref(null)
const editando = ref(null)
const errores = ref({})
const guardando = ref(false)

onMounted(async () => {
  try {
    ;[tipos.value, usadoEn.value] = await Promise.all([catalogo('tipos-relacion', { recargar: true }), api.get(`/productos/${props.producto.id}/usado-en`)])
  } catch (e) { avisarError(e) }
})

const grupos = computed(() => tipos.value.map((t) => ({ tipo: t, lista: props.producto.relaciones.filter((r) => r.tipo_id === t.id) })).filter((g) => g.lista.length))
const tipo = computed(() => tipos.value.find((t) => t.id === editando.value?.tipo_id))

function abrir(r = null) {
  errores.value = {}
  editando.value = r ? { id: r.id, tipo_id: r.tipo_id, destino_id: r.destino.id, cantidad: r.cantidad ?? '', unidad_id: props.unidades.find((u) => u.codigo === r.unidad)?.id ?? null, orden: r.orden }
    : { tipo_id: tipos.value.find((t) => t.activo)?.id ?? null, destino_id: null, cantidad: '', unidad_id: null, orden: 0 }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  const { id, ...d } = editando.value
  const cuerpo = { ...d, cantidad: tipo.value?.con_cantidad && d.cantidad !== '' ? Number(d.cantidad) : null,
    unidad_id: tipo.value?.con_cantidad ? d.unidad_id : null }
  try {
    if (id) await api.patch(`/productos/${props.producto.id}/relaciones/${id}`, cuerpo)
    else await api.post(`/productos/${props.producto.id}/relaciones`, cuerpo)
    avisar('Relación guardada.')
    editando.value = null
    emit('recargar')
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { guardando.value = false }
}

async function borrar(r) {
  if (!await confirmar({ titulo: 'Quitar relación', mensaje: `Se quitará el vínculo con ${r.destino.codigo} · ${r.destino.nombre}.`, accion: 'Quitar', peligro: true })) return
  try {
    await api.del(`/productos/${props.producto.id}/relaciones/${r.id}`)
    avisar('Relación quitada.')
    emit('recargar')
  } catch (e) { avisarError(e) }
}
</script>

<template>
  <div class="pila envoltura">
    <section class="tarjeta">
      <header class="tarjeta-cabeza">
        <div><h2>Relaciones</h2><p>Componentes, sustitutos, accesorios y cualquier otro vínculo configurado.</p></div>
        <button class="btn primario" type="button" :disabled="!tipos.length" @click="abrir()"><Icono nombre="mas" :tam="16" />Relacionar producto</button>
      </header>
      <template v-if="grupos.length">
        <div v-for="g in grupos" :key="g.tipo.id" class="grupo">
          <h3>{{ g.tipo.nombre }}</h3>
          <table class="tabla">
            <thead><tr><th>Producto</th><th v-if="g.tipo.con_cantidad" class="derecha">Cantidad</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
            <tbody>
              <tr v-for="r in g.lista" :key="r.id">
                <td><RouterLink :to="`/productos/${r.destino.id}`"><code>{{ r.destino.codigo }}</code> · {{ r.destino.nombre }}</RouterLink></td>
                <td v-if="g.tipo.con_cantidad" class="derecha num">{{ r.cantidad }} {{ r.unidad || '' }}</td>
                <td class="acciones">
                  <button class="btn fantasma icono chico" type="button" :aria-label="`Editar relación con ${r.destino.nombre}`" @click="abrir(r)"><Icono nombre="editar" :tam="16" /></button>
                  <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Quitar relación con ${r.destino.nombre}`" @click="borrar(r)"><Icono nombre="borrar" :tam="16" /></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <EstadoVacio v-else icono="enlace" titulo="Sin relaciones" texto="Arme listas de materiales, kits, o indique sustitutos y accesorios.">
        <button v-if="tipos.length" class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Relacionar producto</button>
      </EstadoVacio>
    </section>

    <section class="tarjeta">
      <header class="tarjeta-cabeza"><div><h2>Dónde se usa</h2><p>Otros productos que apuntan a este.</p></div></header>
      <ul v-if="usadoEn?.length" class="usado">
        <li v-for="u in usadoEn" :key="u.id">
          <span class="insignia sin-punto">{{ u.nombre }}</span>
          <RouterLink :to="`/productos/${u.origen.id}`"><code>{{ u.origen.codigo }}</code> · {{ u.origen.nombre }}</RouterLink>
          <span v-if="u.cantidad" class="tenue num">× {{ u.cantidad }}</span>
        </li>
      </ul>
      <p v-else-if="usadoEn" class="tenue chico vacio">Ningún otro producto lo usa.</p>
    </section>
  </div>

  <Modal v-if="editando" :titulo="editando.id ? 'Editar relación' : 'Relacionar producto'" ancho="560px" @cerrar="editando = null">
    <form id="form-rel" class="pila" @submit.prevent="guardar">
      <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
      <Campo etiqueta="Tipo de relación" id="r-tipo" obligatorio>
        <select id="r-tipo" v-model="editando.tipo_id" class="control" :disabled="!!editando.id">
          <option v-for="t in tipos.filter((x) => x.activo)" :key="t.id" :value="t.id">{{ t.nombre }}</option>
        </select></Campo>
      <Campo etiqueta="Producto relacionado" id="r-destino" :error="errores.destino_id" obligatorio>
        <SelectorProducto id="r-destino" v-model="editando.destino_id" :excluir="producto.id" :invalido="!!errores.destino_id" /></Campo>
      <div v-if="tipo?.con_cantidad" class="rejilla-2">
        <Campo etiqueta="Cantidad" id="r-cant" :error="errores.cantidad" obligatorio>
          <input id="r-cant" v-model="editando.cantidad" class="control num" type="number" step="any" min="0" required /></Campo>
        <Campo etiqueta="Unidad" id="r-unidad">
          <select id="r-unidad" v-model="editando.unidad_id" class="control">
            <option :value="null">La del producto relacionado</option>
            <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
          </select></Campo>
      </div>
    </form>
    <template #pie>
      <button class="btn" type="button" @click="editando = null">Cancelar</button>
      <button class="btn primario" type="submit" form="form-rel" :disabled="guardando || !editando.destino_id"><span v-if="guardando" class="cargando-btn" />Guardar</button>
    </template>
  </Modal>
</template>

<style scoped>
.envoltura { margin-top: var(--e-2); }
.grupo h3 { padding: var(--e-4) var(--e-5) var(--e-2); color: var(--tinta-2); }
.usado { list-style: none; margin: 0; padding: var(--e-2) var(--e-5) var(--e-4); display: flex; flex-direction: column; gap: var(--e-2); }
.usado li { display: flex; align-items: center; gap: var(--e-3); }
.vacio { padding: var(--e-4) var(--e-5); }
</style>
