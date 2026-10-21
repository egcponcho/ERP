<script setup>
// Elegir categorías por taxonomía: una lista por taxonomía (varias si la taxonomía lo permite).
import { computed, onMounted, ref } from 'vue'
import { catalogo } from '@/nucleo/catalogos.js'

const props = defineProps({ modelValue: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])
const taxonomias = ref([])
const categorias = ref([])

onMounted(async () => {
  ;[taxonomias.value, categorias.value] = await Promise.all([catalogo('taxonomias'), catalogo('categorias')])
})

const activas = computed(() => taxonomias.value.filter((t) => t.activa))
// Las categorías de una taxonomía en orden de árbol, con su ruta como nombre
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
  <div v-if="activas.length" class="rejilla-2">
    <div v-for="t in activas" :key="t.id" class="campo">
      <label :for="`tax-${t.id}`" :class="{ obligatorio: t.obligatoria }">{{ t.nombre }}</label>
      <select v-if="!t.multiple" :id="`tax-${t.id}`" class="control" :value="elegidas(t.id)[0] ?? ''"
              @change="fijar(t.id, $event.target.value ? [Number($event.target.value)] : [])">
        <option value="">Sin categoría</option>
        <option v-for="o in opciones(t.id)" :key="o.id" :value="o.id">{{ o.nombre }}</option>
      </select>
      <div v-else :id="`tax-${t.id}`" class="multiple" role="group" :aria-label="t.nombre">
        <button v-for="o in opciones(t.id)" :key="o.id" type="button" class="opcion" :aria-pressed="elegidas(t.id).includes(o.id)"
                @click="alternar(t.id, o.id)">{{ o.nombre }}</button>
        <span v-if="!opciones(t.id).length" class="tenue chico">Sin categorías.</span>
      </div>
    </div>
  </div>
  <p v-else class="tenue chico">No hay taxonomías configuradas. <RouterLink to="/configuracion/categorias">Configurar categorías</RouterLink></p>
</template>

<style scoped>
.multiple { display: flex; flex-wrap: wrap; gap: 6px; }
.opcion { height: 30px; padding: 0 12px; border-radius: 999px; border: 1px solid var(--borde-control); background: var(--superficie); color: var(--tinta-2); font: inherit; font-size: 13px; cursor: pointer; }
.opcion:hover { border-color: var(--acento); }
.opcion[aria-pressed='true'] { background: var(--acento-claro); border-color: var(--acento); color: var(--acento-texto); font-weight: 550; }
</style>
