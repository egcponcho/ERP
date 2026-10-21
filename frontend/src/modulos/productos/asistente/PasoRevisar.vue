<script setup>
// Último paso: todo se valida en el servidor sin guardar (los códigos y SKU
// reales, los problemas de cada paso) y se elige en qué estado queda el producto.
import { computed, onMounted, ref, watch } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { valorTexto } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'
import { b } from './borrador.js'

const props = defineProps({
  esquema: { type: Object, required: true }, datos: { type: Object, required: true },
  previa: { type: Object, default: null }, errores: { type: Array, default: () => [] }, pasos: { type: Array, required: true }, ocupado: Boolean,
})
const emit = defineEmits(['ir', 'validar'])
const destinos = ref([])
const inicial = computed(() => props.datos.estados.find((e) => e.inicial && e.activo))

onMounted(async () => {
  if (inicial.value) {
    try { destinos.value = await api.get(`${CONFIG}/estados/${inicial.value.id}/transiciones`) } catch { destinos.value = [] }
  }
})
// Estados posibles al crear: el inicial y los que se alcanzan desde él
const estados = computed(() => props.datos.estados.filter((e) => e.activo && (e.id === inicial.value?.id || !destinos.value.length || destinos.value.includes(e.id)))
  .sort((a, b) => a.orden - b.orden))
const elegido = computed(() => b.estadoId ?? inicial.value?.id)
function elegir(e) {
  b.estadoId = e.id === inicial.value?.id ? null : e.id
}
watch(() => b.estadoId, () => emit('validar'))

const PASO = { general: 'Datos generales', caracteristicas: 'Características', variantes: 'Variantes', empaque: 'Empaque y códigos', clasificacion: 'Categorías' }
function pasoDe(campo) {
  if (campo.startsWith('producto.atributos')) return 'caracteristicas'
  if (campo.startsWith('producto.categorias')) return 'clasificacion'
  if (campo.startsWith('producto')) return 'general'
  if (campo.startsWith('variantes')) return 'variantes'
  if (campo.startsWith('presentaciones') || campo.startsWith('identificadores')) return 'empaque'
  return ''
}
// Lo que falta para el estado elegido, con el paso donde se completa
const faltantes = computed(() => props.errores.flatMap((e) => e.faltantes || []).map((f) => ({
  ...f, paso: f.nivel === 'categoria' ? 'clasificacion' : f.nivel === 'variante' ? 'variantes' : 'caracteristicas' })))
const problemas = computed(() => props.errores.filter((e) => !e.faltantes))

const campos = computed(() => props.esquema.campos.filter((c) => c.nivel === 'producto'))
const ejes = computed(() => props.esquema.campos.filter((c) => c.es_eje))
const columnasVariantes = computed(() => [{ clave: 'codigo', texto: 'SKU', fija: true },
  ...ejes.value.map((e) => ({ clave: `n_${e.atributo.codigo}`, texto: e.atributo.nombre })),
  { clave: 'nombre', texto: 'Nombre', filtro: false }])
// Filas con el nombre de cada valor de eje (n_<eje>) para mostrarlo, ordenarlo y filtrarlo
const filasVariantes = computed(() => (props.previa?.variantes || []).map((v, i) => ({ ...v, id: i,
  ...Object.fromEntries(ejes.value.map((e) => [`n_${e.atributo.codigo}`, valorTexto(v.atributos[e.atributo.codigo], e.atributo)])) })))
const tipoId = (id) => props.datos.tiposIdentificador.find((t) => t.id === id)?.nombre
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>¿En qué estado queda?</h2><p>Puede crearlo como borrador y completarlo después, o activarlo ya si la ficha está completa.</p></div>
    </div>
    <div class="tarjetas-eleccion" role="radiogroup" aria-label="Estado del producto">
      <button v-for="e in estados" :key="e.id" type="button" role="radio" class="tarjeta-eleccion" :aria-checked="elegido === e.id" @click="elegir(e)">
        <b>{{ e.nombre }}</b>
        <small>{{ e.operable ? 'Listo para comprar, vender e inventariar.' : e.inicial ? 'Se puede seguir editando; todavía no se usa en operaciones.' : 'Estado de la configuración.' }}</small>
        <span class="insignias"><span v-if="e.exige_completo" class="etiqueta aviso ms-0">Exige ficha completa</span></span>
      </button>
    </div>
  </section>

  <section v-if="ocupado && !previa" class="panel" aria-busy="true"><p class="ayuda">Revisando todo antes de crear…</p>
    <span class="esqueleto mt-chico" style="height: 120px" /></section>

  <section v-if="faltantes.length" class="panel">
    <div class="nota aviso"><Icono nombre="alerta" :tam="16" />
      <div class="crece"><b>Para dejarlo en ese estado falta:</b>
        <ul class="lista-mensajes mt-chico">
          <li v-for="(f, i) in faltantes" :key="i">{{ f.nombre }}<template v-if="f.variante"> (variante {{ f.variante }})</template>
            <button type="button" class="btn-texto" @click="emit('ir', f.paso)">Completar en {{ PASO[f.paso] }}</button></li>
        </ul>
        <p class="mt-chico">O elija un estado que no exija la ficha completa.</p>
      </div>
    </div>
  </section>
  <section v-if="problemas.length" class="panel">
    <div class="nota error" role="alert"><Icono nombre="alerta" :tam="16" />
      <div class="crece"><b>Hay datos por corregir:</b>
        <ul class="lista-mensajes mt-chico">
          <li v-for="(e, i) in problemas" :key="i">{{ e.mensaje }}
            <button v-if="pasoDe(e.campo)" type="button" class="btn-texto" @click="emit('ir', pasoDe(e.campo))">Ir a {{ PASO[pasoDe(e.campo)] }}</button></li>
        </ul>
      </div>
    </div>
  </section>

  <template v-if="previa">
    <div class="nota ok"><Icono nombre="check" :tam="16" /><span>Todo en orden. Al crear se guarda el producto
      <b class="mono">{{ previa.codigo }}</b><template v-if="previa.variantes.length"> con {{ previa.variantes.length }} variantes</template>, en estado <b>{{ previa.estado.nombre }}</b>.</span></div>
    <div class="revision">
      <section class="panel">
        <div class="panel-cabeza"><h2>Datos generales</h2><button type="button" class="btn btn-chico btn-fantasma" @click="emit('ir', 'general')"><Icono nombre="editar" :tam="14" />Cambiar</button></div>
        <dl class="resumen-datos">
          <dt>Código</dt><dd class="mono">{{ previa.codigo }}</dd>
          <dt>Nombre</dt><dd>{{ previa.nombre }}</dd>
          <dt>Tipo</dt><dd>{{ previa.tipo.nombre }}</dd>
          <dt>Unidad</dt><dd>{{ previa.unidad.nombre }}</dd>
          <template v-if="previa.descripcion"><dt>Descripción</dt><dd>{{ previa.descripcion }}</dd></template>
        </dl>
      </section>
      <section v-if="campos.length" class="panel">
        <div class="panel-cabeza"><h2>Características</h2><button type="button" class="btn btn-chico btn-fantasma" @click="emit('ir', 'caracteristicas')"><Icono nombre="editar" :tam="14" />Cambiar</button></div>
        <dl class="resumen-datos">
          <template v-for="c in campos" :key="c.atributo.id"><dt>{{ c.atributo.nombre }}</dt>
            <dd :class="{ apagado: previa.atributos[c.atributo.codigo] === undefined }">{{ previa.atributos[c.atributo.codigo] === undefined ? 'Sin dato' : valorTexto(previa.atributos[c.atributo.codigo], c.atributo) }}</dd></template>
        </dl>
      </section>
      <section class="panel">
        <div class="panel-cabeza"><h2>Empaque, códigos y categorías</h2><button type="button" class="btn btn-chico btn-fantasma" @click="emit('ir', 'empaque')"><Icono nombre="editar" :tam="14" />Cambiar</button></div>
        <dl class="resumen-datos">
          <dt>Presentaciones</dt><dd>{{ previa.presentaciones.map((p) => `${p.nombre} (${p.cantidad} ${previa.unidad.codigo})`).join(', ') || 'Ninguna' }}</dd>
          <dt>Códigos</dt><dd>{{ previa.identificadores.map((x) => `${tipoId(x.tipo_id) || x.tipo} ${x.valor}`).join(', ') || 'Ninguno' }}</dd>
          <dt>Categorías</dt><dd>{{ previa.categorias.map((c) => c.nombre).join(', ') || 'Ninguna' }}</dd>
        </dl>
      </section>
    </div>
    <section v-if="previa.variantes.length" class="panel">
      <div class="panel-cabeza"><div><h2>Variantes que se crean</h2><p>Con su SKU definitivo.</p></div>
        <button type="button" class="btn btn-chico btn-fantasma" @click="emit('ir', 'variantes')"><Icono nombre="editar" :tam="14" />Cambiar</button></div>
      <TablaDatos tabla="asistente-revision" :columnas="columnasVariantes" :filas="filasVariantes" :vistas-guardadas="false" etiqueta="Variantes">
        <template #celda-codigo="{ fila }"><code>{{ fila.codigo }}</code></template>
      </TablaDatos>
    </section>
  </template>
</template>

<style scoped>
.revision { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.revision .panel + .panel { margin-top: 0; }
</style>
