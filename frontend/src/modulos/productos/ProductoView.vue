<script setup>
// Ficha de un producto: encabezado con estado y acciones, aviso de lo que falta y pestañas.
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import Pestanas from '@/componentes/Pestanas.vue'
import PestanaFicha from './PestanaFicha.vue'
import PestanaVariantes from './PestanaVariantes.vue'
import PestanaPresentaciones from './PestanaPresentaciones.vue'
import PestanaIdentificadores from './PestanaIdentificadores.vue'
import PestanaRelaciones from './PestanaRelaciones.vue'
import PestanaRevisiones from './PestanaRevisiones.vue'

const props = defineProps({ id: { type: Number, required: true } })
const route = useRoute()
const router = useRouter()
const producto = ref(null)
const esquema = ref(null)
const unidades = ref([])
const estados = ref([])
const destinos = ref([])
const pestana = ref(route.query.p || 'ficha')
const cambiandoEstado = ref(false)
const publicando = ref(null)
const noExiste = ref(false)

watch(pestana, (p) => router.replace({ query: p === 'ficha' ? {} : { p } }))

async function cargar() {
  try {
    const p = await api.get(`/productos/${props.id}`)
    const [e, u, s, d] = await Promise.all([api.get(`${CONFIG}/tipos-producto/${p.tipo.id}/esquema`), catalogo('unidades'),
      catalogo('estados', { recargar: true }), api.get(`${CONFIG}/estados/${p.estado.id}/transiciones`)])
    ;[producto.value, esquema.value, unidades.value, estados.value, destinos.value] = [p, e, u, s, d]
  } catch (e) {
    if (e.status === 404) noExiste.value = true
    else avisarError(e)
  }
}
onMounted(cargar)

const pestanas = computed(() => {
  const p = producto.value
  const conVariantes = esquema.value?.campos.some((c) => c.es_eje)
  return [
    { id: 'ficha', nombre: 'Ficha' },
    ...(conVariantes || p?.variantes.length ? [{ id: 'variantes', nombre: 'Variantes', cuenta: p?.variantes.length }] : []),
    { id: 'presentaciones', nombre: 'Presentaciones', cuenta: p?.presentaciones.length },
    { id: 'identificadores', nombre: 'Identificadores', cuenta: p?.identificadores.length },
    { id: 'relaciones', nombre: 'Relaciones', cuenta: p?.relaciones.length },
    { id: 'revisiones', nombre: 'Revisiones', cuenta: p?.revision || null },
  ]
})
const estadoActual = computed(() => estados.value.find((e) => e.id === producto.value?.estado.id))
const siguientes = computed(() => estados.value.filter((e) => e.activo && e.id !== producto.value?.estado.id
  && (!destinos.value.length || destinos.value.includes(e.id))))
const tono = (e) => (e?.operable ? 'ok' : e?.inicial ? 'info' : '')

async function cambiarEstado(e) {
  cambiandoEstado.value = false
  try {
    producto.value = await api.post(`/productos/${props.id}/estado`, { estado_id: e.id, version: producto.value.version })
    destinos.value = await api.get(`${CONFIG}/estados/${e.id}/transiciones`)
    avisar(`El producto pasó a ${e.nombre}.`)
  } catch (err) {
    avisarError(err)
    if (err.detalle?.faltantes) producto.value = { ...producto.value, faltantes: err.detalle.faltantes }
  }
}

async function publicar() {
  try {
    const r = await api.post(`/productos/${props.id}/revisiones`, { motivo: publicando.value.motivo || null })
    avisar(`Se publicó la revisión ${r.numero}.`)
    publicando.value = null
    await cargar()
    pestana.value = 'revisiones'
  } catch (e) { avisarError(e) }
}

async function borrar() {
  const ok = await confirmar({ titulo: 'Borrar producto', mensaje: `Se borrará ${producto.value.codigo} con sus variantes, presentaciones e identificadores. Si otro producto lo usa no se podrá: cámbielo a un estado inactivo.`, accion: 'Borrar producto', peligro: true })
  if (!ok) return
  try {
    await api.del(`/productos/${props.id}`)
    avisar('Producto borrado.')
    router.push('/productos')
  } catch (e) { avisarError(e) }
}

function actualizado(p) {
  producto.value = p
}
</script>

<template>
  <div class="pagina">
    <template v-if="producto && esquema">
      <header class="pagina-cabeza">
        <div class="crece">
          <nav class="migas" aria-label="Ruta"><RouterLink to="/productos">Productos</RouterLink><Icono nombre="derecha" :tam="12" />
            <RouterLink :to="`/productos?tipo_id=${producto.tipo.id}`">{{ producto.tipo.nombre }}</RouterLink></nav>
          <div class="titulo">
            <h1>{{ producto.nombre }}</h1>
            <div class="estado-menu">
              <button class="insignia boton-estado" :class="tono(estadoActual)" type="button" :aria-expanded="cambiandoEstado"
                      aria-haspopup="menu" :disabled="!siguientes.length" @click="cambiandoEstado = !cambiandoEstado">
                {{ producto.estado.nombre }}<Icono v-if="siguientes.length" nombre="abajo" :tam="12" />
              </button>
              <div v-if="cambiandoEstado" class="menu" role="menu" @keydown.esc="cambiandoEstado = false">
                <p class="tenue chico">Pasar a</p>
                <button v-for="e in siguientes" :key="e.id" type="button" role="menuitem" @click="cambiarEstado(e)">
                  <span class="insignia" :class="tono(e)">{{ e.nombre }}</span>
                  <span v-if="e.exige_completo" class="tenue chico">exige ficha completa</span>
                </button>
              </div>
            </div>
          </div>
          <p class="meta"><code>{{ producto.codigo }}</code> · {{ producto.unidad.nombre }}
            <template v-if="producto.revision"> · Revisión {{ producto.revision }}</template></p>
        </div>
        <div class="fila">
          <button class="btn" type="button" @click="publicando = { motivo: '' }"><Icono nombre="publicar" :tam="16" />Publicar revisión</button>
          <button class="btn icono peligro" type="button" aria-label="Borrar producto" title="Borrar producto" @click="borrar"><Icono nombre="borrar" :tam="16" /></button>
        </div>
      </header>

      <div v-if="producto.faltantes.length" class="aviso-caja aviso" role="status">
        <Icono nombre="alerta" />
        <div><strong>Ficha incompleta.</strong> Falta completar para pasar a un estado que exige ficha completa:
          <ul><li v-for="(f, i) in producto.faltantes" :key="i">{{ f.nombre }}<template v-if="f.variante"> en la variante <code>{{ f.variante }}</code></template><template v-if="f.nivel === 'categoria'"> (categoría)</template></li></ul>
        </div>
      </div>

      <Pestanas v-model="pestana" :pestanas="pestanas" />
      <div role="tabpanel">
        <PestanaFicha v-if="pestana === 'ficha'" :producto="producto" :esquema="esquema" :unidades="unidades" @actualizado="actualizado" @recargar="cargar" />
        <PestanaVariantes v-else-if="pestana === 'variantes'" :producto="producto" :esquema="esquema" :unidades="unidades" @recargar="cargar" />
        <PestanaPresentaciones v-else-if="pestana === 'presentaciones'" :producto="producto" :unidades="unidades" @recargar="cargar" />
        <PestanaIdentificadores v-else-if="pestana === 'identificadores'" :producto="producto" @recargar="cargar" />
        <PestanaRelaciones v-else-if="pestana === 'relaciones'" :producto="producto" :unidades="unidades" @recargar="cargar" />
        <PestanaRevisiones v-else-if="pestana === 'revisiones'" :producto="producto" @publicar="publicando = { motivo: '' }" />
      </div>
    </template>
    <div v-else-if="noExiste" class="tarjeta tarjeta-cuerpo">
      <h2>Este producto no existe</h2><p class="tenue">Puede que se haya borrado. <RouterLink to="/productos">Volver a productos</RouterLink></p>
    </div>
    <div v-else class="pila" aria-busy="true"><span class="esqueleto" style="width: 320px; height: 28px" /><span class="esqueleto" style="width: 200px" /><span class="esqueleto" style="height: 240px" /></div>

    <Modal v-if="publicando" titulo="Publicar revisión" descripcion="Congela la ficha actual completa como una versión que ya no cambia, con fecha de vigencia." @cerrar="publicando = null">
      <form id="form-publicar" class="pila" @submit.prevent="publicar">
        <div class="campo">
          <label for="motivo">Motivo del cambio</label>
          <textarea id="motivo" v-model="publicando.motivo" class="control" maxlength="500" placeholder="Nueva receta, cambio de proveedor de materia prima…" autofocus />
        </div>
        <p class="tenue chico">La revisión {{ producto.revision + 1 }} quedará vigente desde ahora y la anterior se cerrará.</p>
      </form>
      <template #pie>
        <button class="btn" type="button" @click="publicando = null">Cancelar</button>
        <button class="btn primario" type="submit" form="form-publicar">Publicar revisión {{ producto.revision + 1 }}</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.titulo { display: flex; align-items: center; gap: var(--e-3); flex-wrap: wrap; }
.meta { color: var(--tinta-3); margin-top: 6px; }
.estado-menu { position: relative; }
.boton-estado { border: 0; cursor: pointer; height: 26px; font: inherit; font-size: 12.5px; font-weight: 600; }
.boton-estado:disabled { cursor: default; }
.boton-estado:not(:disabled):hover { filter: brightness(0.96); }
.menu { position: absolute; top: calc(100% + 6px); left: 0; z-index: 20; min-width: 240px; background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio); box-shadow: var(--sombra-media); padding: var(--e-2); display: flex; flex-direction: column; gap: 2px; }
.menu p { padding: 2px var(--e-2) var(--e-1); }
.menu button { display: flex; align-items: center; justify-content: space-between; gap: var(--e-2); padding: 8px; border: 0; border-radius: 6px; background: transparent; cursor: pointer; font: inherit; color: var(--tinta); text-align: left; }
.menu button:hover { background: var(--fila-hover); }
</style>
