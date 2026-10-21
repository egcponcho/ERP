<script setup>
// Crear un tipo de producto sin salir del asistente: nombre, numeración y qué
// características tiene (las que ya existen o nuevas, creadas aquí mismo).
import { computed, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar } from '@/nucleo/avisos.js'
import { TIPOS_DATO } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'
import NuevaCaracteristica from './NuevaCaracteristica.vue'

const props = defineProps({ datos: { type: Object, required: true } })
const emit = defineEmits(['cerrar', 'creado'])
const t = reactive({ nombre: '', codigo: '', padre_id: null, unidad_defecto_id: null, plantilla_codigo: '' })
const codigoTocado = ref(false)
const plantillaTocada = ref(false)
const usos = reactive({}) // atributo_id → { uso: '' | 'producto' | 'variante' | 'eje', obligatorio }
const agregando = ref(false)
const errores = ref({})
const general = ref('')
const ocupado = ref(false)

const USOS = [['', 'No lo usa'], ['producto', 'Dato del producto'], ['eje', 'Distingue variantes'], ['variante', 'Dato de cada variante']]
const COLUMNAS = [
  { clave: 'nombre', texto: 'Característica', fija: true },
  { clave: 'tipo', texto: 'Tipo de dato', valor: (f) => TIPOS_DATO[f.tipo_dato] },
  { clave: 'uso', texto: 'Uso en este tipo', filtro: false, ordenable: false },
  { clave: 'obligatorio', texto: 'Obligatorio', filtro: false, ordenable: false },
]
const creadas = ref([]) // características nuevas creadas aquí (la lista general se recarga al terminar)
const todas = computed(() => [...props.datos.atributos, ...creadas.value.filter((a) => !props.datos.atributos.some((x) => x.id === a.id))])
const filas = computed(() => todas.value.filter((a) => a.activo))
const elegidos = computed(() => Object.entries(usos).filter(([, u]) => u.uso))
const ejes = computed(() => elegidos.value.filter(([, u]) => u.uso === 'eje').map(([id]) => todas.value.find((a) => a.id === Number(id))))

const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '')
function alNombre() {
  if (!codigoTocado.value) t.codigo = norm(t.nombre).toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 30)
  if (!plantillaTocada.value) {
    const pre = norm(t.nombre).toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3)
    t.plantilla_codigo = pre ? `${pre}-{seq:05}` : ''
  }
}
function uso(a) {
  return usos[a.id] || (usos[a.id] = { uso: '', obligatorio: false })
}
function nuevaCreada(a) {
  creadas.value.push(a)
  usos[a.id] = { uso: 'producto', obligatorio: false }
  agregando.value = false
}

async function crear() {
  errores.value = {}
  general.value = ''
  if (!t.nombre.trim()) { errores.value = { nombre: 'Escriba el nombre del tipo.' }; return }
  ocupado.value = true
  try {
    const sku = ejes.value.length ? `{producto}-${ejes.value.map((a) => `{${a.codigo}}`).join('-')}` : null
    const tipo = await api.post(`${CONFIG}/tipos-producto`, { codigo: t.codigo, nombre: t.nombre.trim(), padre_id: t.padre_id,
      unidad_defecto_id: t.unidad_defecto_id, plantilla_codigo: t.plantilla_codigo || null, plantilla_sku: sku })
    let orden = 1
    for (const [id, u] of elegidos.value) {
      await api.post(`${CONFIG}/tipos-producto/${tipo.id}/atributos`, { atributo_id: Number(id), nivel: u.uso === 'producto' ? 'producto' : 'variante',
        es_eje: u.uso === 'eje', obligatorio: u.uso !== 'eje' && u.obligatorio, orden: orden++ })
    }
    avisar(`Se creó el tipo ${tipo.nombre}.`)
    emit('creado', tipo)
  } catch (e) {
    errores.value = e.porCampo
    general.value = e.message
  } finally { ocupado.value = false }
}
</script>

<template>
  <PanelEnLinea titulo="Nuevo tipo de producto" descripcion="Se guarda en la configuración y queda disponible para los próximos productos." @cerrar="emit('cerrar')">
    <div v-if="general" class="nota error mb-3" role="alert"><Icono nombre="alerta" :tam="16" /><span>{{ general }}</span></div>
    <div class="rejilla-campos">
      <label class="campo" :class="{ 'con-error': errores.nombre }"><span class="req">Nombre</span>
        <input v-model="t.nombre" class="entrada" maxlength="100" placeholder="Ej.: Calzado, Químico, Alimento" autofocus @input="alNombre" />
        <small v-if="errores.nombre" class="campo-error">{{ errores.nombre }}</small></label>
      <label class="campo" :class="{ 'con-error': errores.codigo }"><span class="req">Código</span>
        <input v-model="t.codigo" class="entrada mono" maxlength="30" @input="codigoTocado = true" />
        <small v-if="errores.codigo" class="campo-error">{{ errores.codigo }}</small></label>
      <label class="campo"><span>Dentro de</span>
        <select v-model="t.padre_id" class="entrada">
          <option :value="null">Ninguno (tipo principal)</option>
          <option v-for="x in datos.tipos" :key="x.id" :value="x.id">{{ x.nombre }}</option>
        </select>
        <small class="ayuda">Hereda las características del tipo elegido.</small></label>
      <label class="campo"><span>Unidad base</span>
        <select v-model="t.unidad_defecto_id" class="entrada">
          <option :value="null">{{ t.padre_id ? 'La del tipo padre' : 'Elegir al crear cada producto' }}</option>
          <option v-for="u in datos.unidades.filter((x) => x.activa)" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
        </select></label>
      <label class="campo" :class="{ 'con-error': errores.plantilla_codigo }"><span>Numeración automática</span>
        <input v-model="t.plantilla_codigo" class="entrada mono" maxlength="60" placeholder="CAL-{seq:05}" @input="plantillaTocada = true" />
        <small v-if="errores.plantilla_codigo" class="campo-error">{{ errores.plantilla_codigo }}</small>
        <small v-else class="ayuda">{seq:05} = 00001, 00002… Vacío: el código se escribe a mano.</small></label>
    </div>

    <div class="fila-flex entre mt">
      <div><h3>Características del tipo</h3>
        <p class="ayuda">Indique cuáles usa y cómo. Las que «distinguen variantes» crean un SKU por combinación (talla × color).</p></div>
      <button v-if="!agregando" type="button" class="btn btn-chico" @click="agregando = true"><Icono nombre="mas" :tam="14" />Nueva característica</button>
    </div>
    <NuevaCaracteristica v-if="agregando" :datos="datos" class="mt-chico" @cerrar="agregando = false" @creada="nuevaCreada" />

    <TablaDatos v-if="filas.length" class="mt-chico" tabla="asistente-caracteristicas" :columnas="COLUMNAS" :filas="filas" :vistas-guardadas="false"
                :por-pagina="10" orden-inicial="nombre:asc" etiqueta="Características disponibles" :clase-fila="(f) => ({ seleccionada: !!uso(f).uso })">
      <template #celda-nombre="{ fila }"><b>{{ fila.nombre }}</b><span class="sub">{{ fila.opciones.map((o) => o.nombre).slice(0, 5).join(', ') }}</span></template>
      <template #celda-tipo="{ fila }">{{ TIPOS_DATO[fila.tipo_dato] }}<span v-if="fila.unidad_defecto" class="sub">en {{ fila.unidad_defecto }}</span></template>
      <template #celda-uso="{ fila }">
        <select v-model="uso(fila).uso" class="entrada entrada-chica" :aria-label="`Uso de ${fila.nombre}`">
          <option v-for="[v, n] in USOS" :key="v" :value="v" :disabled="v === 'eje' && fila.tipo_dato === 'opciones'">{{ n }}</option>
        </select>
      </template>
      <template #celda-obligatorio="{ fila }">
        <label v-if="uso(fila).uso && uso(fila).uso !== 'eje'" class="check"><input v-model="uso(fila).obligatorio" type="checkbox" :aria-label="`${fila.nombre} obligatorio`" />Sí</label>
        <span v-else-if="uso(fila).uso === 'eje'" class="apagado">Siempre</span>
      </template>
    </TablaDatos>
    <p v-else-if="!agregando" class="ayuda mt-chico">Todavía no hay características. Cree la primera con «Nueva característica».</p>

    <template #pie>
      <span class="ayuda separar">{{ elegidos.length }} características elegidas<template v-if="ejes.length"> · variantes por {{ ejes.map((a) => a.nombre.toLowerCase()).join(' y ') }}</template></span>
      <button type="button" class="btn" @click="emit('cerrar')">Cancelar</button>
      <button type="button" class="btn btn-primario" :disabled="ocupado" @click="crear"><Icono nombre="check" :tam="16" />Crear tipo y continuar</button>
    </template>
  </PanelEnLinea>
</template>
