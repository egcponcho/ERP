<script setup>
// Alta rápida de una característica (atributo) en la misma pantalla: nombre,
// tipo de dato y, según el tipo, sus opciones o su unidad. Las reglas finas
// (mínimos, formatos) se ajustan después en Configuración → Características.
import { computed, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { TIPOS_DATO } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'

defineProps({ datos: { type: Object, required: true } })
const emit = defineEmits(['cerrar', 'creada'])
const f = reactive({ nombre: '', tipo_dato: 'opcion', opciones: '', magnitud_id: null, unidad_defecto_id: null })
const errores = ref({})
const general = ref('')
const ocupado = ref(false)
const conOpciones = computed(() => ['opcion', 'opciones'].includes(f.tipo_dato))
const esNumero = computed(() => ['entero', 'decimal'].includes(f.tipo_dato))
const SIMPLES = ['opcion', 'opciones', 'texto', 'decimal', 'entero', 'booleano', 'fecha']

const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '')
const listaOpciones = computed(() => [...new Set(f.opciones.split(/[,\n]/).map((x) => x.trim()).filter(Boolean))])

async function crear() {
  errores.value = {}
  general.value = ''
  if (!f.nombre.trim()) { errores.value = { nombre: 'Escriba el nombre.' }; return }
  if (conOpciones.value && !listaOpciones.value.length) { errores.value = { opciones: 'Escriba al menos una opción.' }; return }
  ocupado.value = true
  const codigo = norm(f.nombre).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').replace(/^(\d)/, 'a_$1').slice(0, 40)
  try {
    const a = await api.post(`${CONFIG}/atributos`, {
      codigo, nombre: f.nombre.trim(), tipo_dato: f.tipo_dato,
      magnitud_id: esNumero.value ? f.magnitud_id : null, unidad_defecto_id: esNumero.value && f.magnitud_id ? f.unidad_defecto_id : null,
      opciones: conOpciones.value ? listaOpciones.value.map((o, i) => ({
        codigo: norm(o).toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 40) || `OP${i + 1}`, nombre: o, orden: i + 1 })) : [],
    })
    emit('creada', a)
  } catch (e) {
    errores.value = e.porCampo
    general.value = e.message
  } finally { ocupado.value = false }
}
</script>

<template>
  <form class="nueva-caracteristica" @submit.prevent="crear" @keydown.esc.stop="emit('cerrar')">
    <div v-if="general" class="nota error"><Icono nombre="alerta" :tam="16" /><span>{{ general }}</span></div>
    <div class="rejilla-campos">
      <label class="campo" :class="{ 'con-error': errores.nombre || errores.codigo }"><span class="req">Nombre</span>
        <input v-model="f.nombre" class="entrada" maxlength="100" placeholder="Ej.: Color, Talla, Peso neto" autofocus />
        <small v-if="errores.nombre || errores.codigo" class="campo-error">{{ errores.nombre || errores.codigo }}</small></label>
      <label class="campo"><span class="req">Cómo se captura</span>
        <select v-model="f.tipo_dato" class="entrada">
          <option v-for="k in SIMPLES" :key="k" :value="k">{{ TIPOS_DATO[k] }}</option>
        </select></label>
      <label v-if="conOpciones" class="campo col-completa" :class="{ 'con-error': errores.opciones }"><span class="req">Opciones</span>
        <input v-model="f.opciones" class="entrada" placeholder="Separadas por coma: Negro, Blanco, Café" />
        <small v-if="errores.opciones" class="campo-error">{{ errores.opciones }}</small>
        <small v-else-if="listaOpciones.length" class="ayuda">{{ listaOpciones.length }} opciones</small></label>
      <template v-if="esNumero">
        <label class="campo"><span>Se mide en</span>
          <select v-model="f.magnitud_id" class="entrada" @change="f.unidad_defecto_id = datos.unidades.find((u) => u.magnitud_id === f.magnitud_id && u.factor === 1)?.id ?? null">
            <option :value="null">Sin unidad (solo número)</option>
            <option v-for="m in datos.magnitudes.filter((x) => x.activa)" :key="m.id" :value="m.id">{{ m.nombre }}</option>
          </select></label>
        <label v-if="f.magnitud_id" class="campo"><span>Unidad habitual</span>
          <select v-model="f.unidad_defecto_id" class="entrada">
            <option v-for="u in datos.unidades.filter((x) => x.magnitud_id === f.magnitud_id)" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
          </select></label>
      </template>
    </div>
    <div class="fila-flex">
      <span class="ayuda separar">Las reglas (mínimos, formato) se ajustan después en Configuración.</span>
      <button type="button" class="btn btn-chico btn-fantasma" @click="emit('cerrar')">Cancelar</button>
      <button type="submit" class="btn btn-chico btn-primario" :disabled="ocupado">Agregar característica</button>
    </div>
  </form>
</template>

<style scoped>
.nueva-caracteristica { display: flex; flex-direction: column; gap: 12px; padding: 14px; border: 1px dashed var(--acento-medio); border-radius: var(--radio); background: var(--acento-claro); }
</style>
