<script setup>
// Ficha de un producto: encabezado de documento (código, estado, acciones),
// lo que falta para completarlo y sus pestañas. Nada se abre en ventanas: se
// edita en la misma página.
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { claseEstado, fecha } from '@/nucleo/formato.js'
import { fijarTitulo } from '@/nucleo/migas.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
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
const menuEstado = ref(false)
const publicando = ref(null)
const noExiste = ref(false)

watch(pestana, (p) => router.replace({ query: p === 'ficha' ? {} : { p } }))

async function cargar() {
  try {
    const p = await api.get(`/productos/${props.id}`)
    const [e, u, s, d] = await Promise.all([api.get(`${CONFIG}/tipos-producto/${p.tipo.id}/esquema`), catalogo('unidades'),
      catalogo('estados', { recargar: true }), api.get(`${CONFIG}/estados/${p.estado.id}/transiciones`)])
    ;[producto.value, esquema.value, unidades.value, estados.value, destinos.value] = [p, e, u, s, d]
    fijarTitulo(p.nombre)
  } catch (e) {
    if (e.status === 404) noExiste.value = true
    else avisarError(e)
  }
}
onMounted(cargar)
watch(() => props.id, () => { producto.value = null; cargar() })

const pestanas = computed(() => {
  const p = producto.value
  return [
    { id: 'ficha', nombre: 'Ficha', cuenta: p?.faltantes.length || null, alerta: true },
    ...(esquema.value?.campos.some((c) => c.es_eje) || p?.variantes.length ? [{ id: 'variantes', nombre: 'Variantes', cuenta: p?.variantes.length }] : []),
    { id: 'presentaciones', nombre: 'Presentaciones', cuenta: p?.presentaciones.length },
    { id: 'identificadores', nombre: 'Códigos', cuenta: p?.identificadores.length },
    { id: 'relaciones', nombre: 'Relaciones', cuenta: p?.relaciones.length },
    { id: 'revisiones', nombre: 'Revisiones', cuenta: p?.revision },
  ]
})
const estadoActual = computed(() => estados.value.find((e) => e.id === producto.value?.estado.id))
const siguientes = computed(() => estados.value.filter((e) => e.activo && e.id !== producto.value?.estado.id
  && (!destinos.value.length || destinos.value.includes(e.id))))

async function cambiarEstado(e) {
  menuEstado.value = false
  try {
    producto.value = await api.post(`/productos/${props.id}/estado`, { estado_id: e.id, version: producto.value.version })
    destinos.value = await api.get(`${CONFIG}/estados/${e.id}/transiciones`)
    avisar(`El producto pasó a ${e.nombre}.`)
  } catch (err) {
    avisarError(err)
    if (err.detalle?.faltantes) { producto.value = { ...producto.value, faltantes: err.detalle.faltantes }; pestana.value = 'ficha' }
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
  try {
    await api.del(`/productos/${props.id}`)
    avisar(`Se borró ${producto.value.codigo}.`)
    router.push('/productos/catalogo')
  } catch (e) { avisarError(e) }
}
</script>

<template>
  <div>
    <template v-if="producto && esquema">
      <header class="doc-cabeza">
        <div class="doc-fila">
          <span class="doc-numero mono">{{ producto.codigo }}</span>
          <div class="estado-menu" @keydown.esc="menuEstado = false">
            <button type="button" class="estado boton-estado" :class="claseEstado(estadoActual)" :aria-expanded="menuEstado" aria-haspopup="menu"
                    :disabled="!siguientes.length" :title="siguientes.length ? 'Cambiar estado' : ''" @click="menuEstado = !menuEstado">
              <span class="estado-marca" />{{ producto.estado.nombre }}<Icono v-if="siguientes.length" nombre="abajo" :tam="12" /></button>
            <div v-if="menuEstado" v-flotante class="menu-estado" role="menu">
              <p class="ayuda">Pasar a</p>
              <button v-for="e in siguientes" :key="e.id" type="button" role="menuitem" @click="cambiarEstado(e)">
                <span class="estado" :class="claseEstado(e)"><span class="estado-marca" />{{ e.nombre }}</span>
                <small v-if="e.exige_completo" class="ayuda">exige ficha completa</small>
              </button>
            </div>
          </div>
          <div class="doc-acciones">
            <button type="button" class="btn" @click="publicando = { motivo: '' }"><Icono nombre="publicar" :tam="16" />Publicar revisión</button>
            <BotonConfirmar :etiqueta="`Borrar ${producto.codigo}`" pregunta="¿Borrar el producto?" texto="Borrar" @confirmar="borrar" />
          </div>
        </div>
        <div class="doc-sub">{{ producto.nombre }}</div>
        <div class="doc-meta">
          <span>Tipo <b><RouterLink :to="`/productos/configuracion/tipos/${producto.tipo.id}`">{{ producto.tipo.nombre }}</RouterLink></b></span>
          <span>Unidad <b>{{ producto.unidad.nombre }}</b></span>
          <span v-if="producto.revision">Revisión <b>{{ producto.revision }}</b></span>
          <span>Modificado <b>{{ fecha(producto.actualizado_en) }}</b></span>
        </div>
      </header>

      <PanelEnLinea v-if="publicando" titulo="Publicar revisión" descripcion="Congela la ficha completa como una versión fija, con fecha de vigencia." @cerrar="publicando = null">
        <label class="campo"><span>Motivo del cambio</span>
          <input v-model="publicando.motivo" class="entrada" maxlength="500" placeholder="Nueva receta, cambio de material…" autofocus @keydown.enter="publicar" /></label>
        <template #pie>
          <span class="ayuda separar">La revisión {{ producto.revision + 1 }} queda vigente desde ahora y la anterior se cierra.</span>
          <button type="button" class="btn" @click="publicando = null">Cancelar</button>
          <button type="button" class="btn btn-primario" @click="publicar"><Icono nombre="publicar" :tam="16" />Publicar revisión {{ producto.revision + 1 }}</button>
        </template>
      </PanelEnLinea>

      <div v-if="producto.faltantes.length" class="nota aviso mb-3" role="status">
        <Icono nombre="alerta" :tam="16" />
        <div><b>Ficha incompleta.</b> Para un estado que exige ficha completa falta:
          {{ producto.faltantes.map((f) => f.nombre + (f.variante ? ` (${f.variante})` : '')).join(', ') }}.</div>
      </div>

      <Pestanas v-model="pestana" :pestanas="pestanas" />
      <div role="tabpanel">
        <PestanaFicha v-if="pestana === 'ficha'" :producto="producto" :esquema="esquema" :unidades="unidades" @actualizado="(p) => (producto = p)" @recargar="cargar" />
        <PestanaVariantes v-else-if="pestana === 'variantes'" :producto="producto" :esquema="esquema" :unidades="unidades" @recargar="cargar" />
        <PestanaPresentaciones v-else-if="pestana === 'presentaciones'" :producto="producto" :unidades="unidades" @recargar="cargar" />
        <PestanaIdentificadores v-else-if="pestana === 'identificadores'" :producto="producto" @recargar="cargar" />
        <PestanaRelaciones v-else-if="pestana === 'relaciones'" :producto="producto" :unidades="unidades" @recargar="cargar" />
        <PestanaRevisiones v-else-if="pestana === 'revisiones'" :producto="producto" @publicar="publicando = { motivo: '' }" />
      </div>
    </template>
    <div v-else-if="noExiste" class="panel">
      <h2>Este producto no existe</h2><p class="ayuda mt-chico">Puede que se haya borrado. <RouterLink to="/productos/catalogo">Volver al catálogo</RouterLink></p>
    </div>
    <div v-else class="doc-cabeza" aria-busy="true"><span class="esqueleto" style="width: 220px; height: 26px" /><span class="esqueleto mt-chico" style="width: 320px; height: 14px" /></div>
  </div>
</template>

<style scoped>
.estado-menu { position: relative; }
.boton-estado { border: 0; cursor: pointer; font: inherit; font-size: 0.8rem; font-weight: 650; line-height: 1.9; }
.boton-estado:disabled { cursor: default; }
.boton-estado:not(:disabled):hover { filter: brightness(0.97); }
.menu-estado { min-width: 240px; background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio-panel); box-shadow: var(--sombra-flotante); padding: 6px; display: flex; flex-direction: column; gap: 2px; }
.menu-estado p { padding: 4px 8px; }
.menu-estado button { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px; border: 0; border-radius: 6px; background: none; cursor: pointer; font: inherit; color: inherit; text-align: start; }
.menu-estado button:hover { background: var(--fila-hover); }
</style>
