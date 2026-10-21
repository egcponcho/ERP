<script setup>
// Control para un atributo según su tipo de dato. Lo arma el esquema del tipo de
// producto: ninguna pantalla conoce los atributos de un rubro.
import { computed } from 'vue'
import Campo from './Campo.vue'
import SelectorProducto from './SelectorProducto.vue'
import Icono from './Icono.vue'

const props = defineProps({
  campo: { type: Object, required: true }, // {atributo, obligatorio, es_eje, heredado_de…}
  modelValue: { type: [String, Number, Boolean, Array, Object], default: null },
  unidades: { type: Array, default: () => [] },
  error: { type: String, default: '' },
  idBase: { type: String, default: 'attr' },
})
const emit = defineEmits(['update:modelValue'])
const a = computed(() => props.campo.atributo)
const id = computed(() => `${props.idBase}-${a.value.codigo}`)
const opciones = computed(() => (a.value.opciones || []).filter((o) => o.activa || [].concat(props.modelValue).includes(o.codigo)))
const unidadesMagnitud = computed(() => props.unidades.filter((u) => u.magnitud_id === a.value.magnitud_id && u.activa))
const conUnidad = computed(() => ['entero', 'decimal'].includes(a.value.tipo_dato) && a.value.magnitud_id)

const ayuda = computed(() => {
  const r = a.value.reglas || {}
  const partes = []
  if (a.value.descripcion) partes.push(a.value.descripcion)
  if (r.minimo !== undefined && r.maximo !== undefined) partes.push(`Entre ${r.minimo} y ${r.maximo}${a.value.unidad_defecto ? ` ${a.value.unidad_defecto}` : ''}`)
  else if (r.minimo !== undefined) partes.push(`Mínimo ${r.minimo}`)
  else if (r.maximo !== undefined) partes.push(`Máximo ${r.maximo}`)
  if (r.decimales !== undefined) partes.push(`hasta ${r.decimales} decimales`)
  if (r.patron) partes.push(`formato ${r.patron}`)
  return partes.join(' · ')
})

const valorNumero = computed(() => (conUnidad.value ? props.modelValue?.valor ?? '' : props.modelValue ?? ''))
const unidad = computed(() => props.modelValue?.unidad || a.value.unidad_defecto || unidadesMagnitud.value[0]?.codigo || '')

function numero(v) {
  const limpio = v === '' ? null : v
  if (conUnidad.value) emit('update:modelValue', limpio === null ? null : { valor: limpio, unidad: unidad.value })
  else emit('update:modelValue', limpio)
}
function cambiarUnidad(u) {
  emit('update:modelValue', valorNumero.value === '' ? null : { valor: valorNumero.value, unidad: u })
}
function alternar(codigo) {
  const actual = [...(props.modelValue || [])]
  const i = actual.indexOf(codigo)
  if (i >= 0) actual.splice(i, 1)
  else actual.push(codigo)
  emit('update:modelValue', actual.length ? actual : null)
}
</script>

<template>
  <Campo :etiqueta="a.nombre" :id="id" :ayuda="ayuda" :error="error" :obligatorio="campo.obligatorio || campo.es_eje">
    <template #etiqueta>
      {{ a.nombre }}
      <span v-if="campo.heredado_de" class="heredado" :title="`Heredado del tipo ${campo.heredado_de}`"><Icono nombre="heredado" :tam="13" /></span>
    </template>

    <input v-if="a.tipo_dato === 'texto'" :id="id" class="control" :class="{ invalido: error }" type="text"
           :value="modelValue ?? ''" :maxlength="a.reglas?.longitud_max || 1000" :aria-invalid="!!error"
           @input="emit('update:modelValue', $event.target.value || null)" />

    <div v-else-if="['entero', 'decimal'].includes(a.tipo_dato)" class="numero">
      <input :id="id" class="control num" :class="{ invalido: error }" type="number" inputmode="decimal"
             :step="a.tipo_dato === 'entero' ? 1 : 'any'" :value="valorNumero" :aria-invalid="!!error"
             @input="numero($event.target.value)" />
      <select v-if="conUnidad" class="control unidad" :value="unidad" :aria-label="`Unidad de ${a.nombre}`"
              @change="cambiarUnidad($event.target.value)">
        <option v-for="u in unidadesMagnitud" :key="u.id" :value="u.codigo">{{ u.simbolo || u.codigo }}</option>
      </select>
    </div>

    <label v-else-if="a.tipo_dato === 'booleano'" class="interruptor">
      <input :id="id" type="checkbox" :checked="!!modelValue" @change="emit('update:modelValue', $event.target.checked)" />
      {{ modelValue ? 'Sí' : 'No' }}
    </label>

    <input v-else-if="a.tipo_dato === 'fecha'" :id="id" class="control" :class="{ invalido: error }" type="date"
           :value="modelValue ?? ''" :min="a.reglas?.minimo" :max="a.reglas?.maximo"
           @input="emit('update:modelValue', $event.target.value || null)" />

    <select v-else-if="a.tipo_dato === 'opcion'" :id="id" class="control" :class="{ invalido: error }" :value="modelValue ?? ''"
            @change="emit('update:modelValue', $event.target.value || null)">
      <option value="">Sin elegir</option>
      <option v-for="o in opciones" :key="o.codigo" :value="o.codigo">{{ o.nombre }}</option>
    </select>

    <div v-else-if="a.tipo_dato === 'opciones'" :id="id" class="multiple" role="group" :aria-label="a.nombre">
      <button v-for="o in opciones" :key="o.codigo" type="button" class="opcion" :aria-pressed="(modelValue || []).includes(o.codigo)"
              @click="alternar(o.codigo)">
        <Icono v-if="(modelValue || []).includes(o.codigo)" nombre="check" :tam="14" />{{ o.nombre }}
      </button>
    </div>

    <SelectorProducto v-else-if="a.tipo_dato === 'referencia' && a.entidad_referencia === 'producto'" :id="id"
                      :model-value="modelValue" :invalido="!!error" @update:model-value="emit('update:modelValue', $event)" />
    <input v-else :id="id" class="control num" type="number" :value="modelValue ?? ''" placeholder="Id del registro"
           @input="emit('update:modelValue', $event.target.value ? Number($event.target.value) : null)" />
  </Campo>
</template>

<style scoped>
.numero { display: flex; gap: var(--e-2); }
.numero .unidad { width: 92px; flex: none; }
.heredado { color: var(--tinta-3); display: inline-flex; }
.multiple { display: flex; flex-wrap: wrap; gap: 6px; }
.opcion { display: inline-flex; align-items: center; gap: 4px; height: 30px; padding: 0 12px; border-radius: 999px; border: 1px solid var(--borde-control); background: var(--superficie); color: var(--tinta-2); font: inherit; font-size: 13px; cursor: pointer; transition: all 0.15s; }
.opcion:hover { border-color: var(--acento); }
.opcion[aria-pressed='true'] { background: var(--acento-claro); border-color: var(--acento); color: var(--acento-texto); font-weight: 550; }
</style>
