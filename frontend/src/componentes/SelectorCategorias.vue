<script setup>
// Elegir categorías por taxonomía: una lista por taxonomía, o pastillas si la taxonomía admite varias.
import { computed, onMounted, ref } from 'vue'
import { catalogo } from '@/nucleo/catalogos.js'

const props = defineProps({ modelValue: { type: Array, required: true }, errores: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:modelValue'])
const taxonomias = ref(null)
const categorias = ref([])

onMounted(async () => {
  ;[taxonomias.value, categorias.value] = await Promise.all([catalogo('taxonomias', { recargar: true }), catalogo('categorias', { recargar: true })])
})

const activas = computed(() => (taxonomias.value || []).filter((t) => t.activa))
function opciones(taxId) {
  const de = categorias.value.filter((c) => c.taxonomia_id === taxId && c.activa)
  const ruta = (c) => {
    const r = []
    let x = c
    while (x) { r.unshift(x.nombre); x = de.find((p) => p.id === x.padre_id) }
    return r.join(' › ')
  }
  return de.map((c) => ({ id: c.id, nombre: ruta(c) })).sort((a, b) => a.nombre.localeCompare(b.nombre))
}
const elegidas = (taxId) => props.modelValue.filter((id) => categorias.value.find((c) => c.id === id)?.taxonomia_id === taxId)
function fijar(taxId, ids) {
  const otras = props.modelValue.filter((id) => categorias.value.find((c) => c.id === id)?.taxonomia_id !== taxId)
  emit('update:modelValue', [...otras, ...ids])
}
function alternar(taxId, id) {
  const actual = elegidas(taxId)
  fijar(taxId, actual.includes(id) ? actual.filter((x) => x !== id) : [...actual, id])
}
</script>

<template>
  <div v-if="activas.length" class="rejilla-campos">
    <div v-for="t in activas" :key="t.id" class="campo" :class="{ 'col-completa': t.multiple }">
      <label :for="`tax-${t.id}`"><span :class="{ req: t.obligatoria }">{{ t.nombre }}</span>
        <small v-if="t.multiple" class="ayuda"> · puede elegir varias</small></label>
      <select v-if="!t.multiple" :id="`tax-${t.id}`" class="entrada" :value="elegidas(t.id)[0] ?? ''"
              @change="fijar(t.id, $event.target.value ? [Number($event.target.value)] : [])">
        <option value="">Sin categoría</option>
        <option v-for="o in opciones(t.id)" :key="o.id" :value="o.id">{{ o.nombre }}</option>
      </select>
      <div v-else :id="`tax-${t.id}`" class="opciones-chips" role="group" :aria-label="t.nombre">
        <button v-for="o in opciones(t.id)" :key="o.id" type="button" class="opcion-chip" :aria-pressed="elegidas(t.id).includes(o.id)"
                @click="alternar(t.id, o.id)">{{ o.nombre }}</button>
        <span v-if="!opciones(t.id).length" class="ayuda">Sin categorías.</span>
      </div>
    </div>
  </div>
  <p v-else-if="taxonomias" class="ayuda">No hay categorías configuradas. Se pueden crear en Configuración → Categorías.</p>
</template>
