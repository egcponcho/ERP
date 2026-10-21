<script setup>
// Ficha: datos generales, características (según el tipo) y categorías. Se lee
// y se edita en el mismo lugar.
import { computed, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { valorTexto } from '@/nucleo/formato.js'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import SelectorCategorias from '@/componentes/SelectorCategorias.vue'

const props = defineProps({ producto: { type: Object, required: true }, esquema: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['actualizado', 'recargar'])
const editando = ref(null)
const errores = ref({})
const general = ref(null)
const guardando = ref(false)
const gruposAtributo = ref([])
catalogo('grupos-atributo').then((g) => (gruposAtributo.value = g)).catch(() => {})

const campos = computed(() => props.esquema.campos.filter((c) => c.nivel === 'producto'))
const fuera = computed(() => Object.entries(props.producto.atributos_fuera_de_esquema || {}))
const grupos = computed(() => {
  const res = new Map()
  for (const c of campos.value) {
    const g = c.atributo.grupo_id ?? 0
    if (!res.has(g)) res.set(g, [])
    res.get(g).push(c)
  }
  return [...res.entries()]
})
const nombreGrupo = (id) => gruposAtributo.value.find((g) => g.id === id)?.nombre || 'Otros datos'
const faltan = computed(() => new Set(props.producto.faltantes.filter((f) => f.nivel === 'producto').map((f) => f.atributo)))

function editar() {
  errores.value = {}
  general.value = null
  const p = props.producto
  editando.value = { nombre: p.nombre, codigo: p.codigo, descripcion: p.descripcion || '', unidad_id: p.unidad.id,
    atributos: JSON.parse(JSON.stringify(p.atributos)), categorias: p.categorias.map((c) => c.id) }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  general.value = null
  const e = editando.value
  const atributos = Object.fromEntries(campos.value.map((c) => {
    const v = e.atributos[c.atributo.codigo]
    return [c.atributo.codigo, v === '' || (Array.isArray(v) && !v.length) ? null : v ?? null]
  }))
  try {
    const p = await api.patch(`/productos/${props.producto.id}`, { version: props.producto.version, nombre: e.nombre, codigo: e.codigo,
      descripcion: e.descripcion || null, unidad_id: e.unidad_id, atributos, categorias: e.categorias })
    emit('actualizado', p)
    editando.value = null
    avisar('Ficha guardada.')
  } catch (err) {
    errores.value = err.porCampo
    for (const f of err.detalle?.faltantes || []) if (f.nivel === 'producto') errores.value[`atributos.${f.atributo}`] = 'Obligatorio en el estado actual.'
    general.value = err.status === 409 && err.detalle?.version_actual
      ? { message: 'Otra persona guardó cambios mientras usted editaba. Recargue para ver la versión actual (perderá lo que no guardó).', recargar: true } : err
  } finally { guardando.value = false }
}
const msj = (k) => (errores.value[k] || '').replace(/^[^:]+: /, '')
</script>

<template>
  <form v-if="editando" class="panel" novalidate @submit.prevent="guardar">
    <div class="panel-cabeza"><div><h2>Editar ficha</h2><p>Los cambios se guardan juntos.</p></div></div>
    <div v-if="general" class="nota error mb-3" role="alert"><Icono nombre="alerta" :tam="16" />
      <div class="crece">{{ general.message }}
        <ul v-if="general.detalle?.faltantes" class="lista-mensajes mt-chico"><li v-for="(x, i) in general.detalle.faltantes" :key="i">{{ x.nombre }}</li></ul>
        <button v-if="general.recargar" class="btn btn-chico mt-chico" type="button" @click="editando = null; emit('recargar')">Recargar</button></div>
    </div>
    <h3 class="resumen-titulo">Datos generales</h3>
    <div class="rejilla-campos">
      <label class="campo" :class="{ 'con-error': errores.nombre }"><span class="req">Nombre</span><input v-model="editando.nombre" class="entrada" maxlength="200" />
        <small v-if="errores.nombre" class="campo-error">{{ errores.nombre }}</small></label>
      <label class="campo" :class="{ 'con-error': errores.codigo }"><span class="req">Código</span><input v-model="editando.codigo" class="entrada mono" maxlength="60" />
        <small v-if="errores.codigo" class="campo-error">{{ errores.codigo }}</small><small v-else class="ayuda">Cambiarlo no cambia los SKU ya creados.</small></label>
      <label class="campo"><span class="req">Unidad base</span>
        <select v-model="editando.unidad_id" class="entrada"><option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option></select></label>
      <label class="campo col-completa"><span>Descripción</span><textarea v-model="editando.descripcion" class="entrada" rows="3" /></label>
    </div>
    <template v-if="campos.length">
      <h3 class="resumen-titulo mt">Características</h3>
      <div class="rejilla-campos">
        <CampoAtributo v-for="c in campos" :key="c.atributo.id" v-model="editando.atributos[c.atributo.codigo]" :campo="c" :unidades="unidades"
                       :error="msj(`atributos.${c.atributo.codigo}`)" id-base="ficha" />
      </div>
    </template>
    <h3 class="resumen-titulo mt">Categorías</h3>
    <SelectorCategorias v-model="editando.categorias" />
    <div class="en-linea-pie">
      <button class="btn" type="button" @click="editando = null">Cancelar</button>
      <button class="btn btn-primario" type="submit" :disabled="guardando"><Icono nombre="check" :tam="16" />Guardar cambios</button>
    </div>
  </form>

  <div v-else class="ficha">
    <section class="panel">
      <div class="panel-cabeza">
        <h2>Características</h2>
        <button class="btn" type="button" @click="editar"><Icono nombre="editar" :tam="16" />Editar ficha</button>
      </div>
      <p v-if="producto.descripcion" class="descripcion">{{ producto.descripcion }}</p>
      <div v-for="[g, lista] in grupos" :key="g" class="grupo">
        <p v-if="grupos.length > 1" class="resumen-titulo">{{ g ? nombreGrupo(g) : 'Generales' }}</p>
        <div class="doc-datos">
          <div v-for="c in lista" :key="c.atributo.id" class="dato"><span :class="{ req: c.obligatorio }">{{ c.atributo.nombre }}</span>
            <b v-if="producto.atributos[c.atributo.codigo] !== undefined">{{ valorTexto(producto.atributos[c.atributo.codigo], c.atributo) }}</b>
            <span v-else class="valor" :class="faltan.has(c.atributo.codigo) ? 'texto-error' : 'apagado'">{{ faltan.has(c.atributo.codigo) ? 'Falta' : 'Sin dato' }}</span>
          </div>
        </div>
      </div>
      <p v-if="!campos.length" class="ayuda">El tipo {{ producto.tipo.nombre }} no tiene características del producto.
        <RouterLink :to="`/productos/configuracion/tipos/${producto.tipo.id}`">Configurar el tipo</RouterLink></p>
      <div v-if="fuera.length" class="nota info mt"><Icono nombre="info" :tam="16" />
        <span>Valores que se conservan aunque el tipo ya no tenga esas características: {{ fuera.map(([k, v]) => `${k} = ${valorTexto(v)}`).join('; ') }}</span></div>
    </section>
    <section class="panel">
      <div class="panel-cabeza"><h2>Categorías</h2></div>
      <div v-if="producto.categorias.length" class="insignias">
        <span v-for="c in producto.categorias" :key="c.id" class="etiqueta acento ms-0" :title="c.taxonomia">{{ c.nombre }}</span>
      </div>
      <p v-else class="ayuda">Sin categorías. <button type="button" class="btn-texto" @click="editar">Asignar</button></p>
    </section>
  </div>
</template>

<style scoped>
.ficha { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }
.ficha .panel + .panel { margin-top: 0; }
@media (max-width: 1000px) { .ficha { grid-template-columns: 1fr; } }
.descripcion { color: var(--tinta-2); white-space: pre-line; margin-bottom: 12px; }
.grupo + .grupo { margin-top: 16px; }
.grupo .doc-datos { margin-top: 0; padding-top: 0; border-top: 0; }
</style>
