<script setup>
// Pestañas con navegación por teclado (flechas izquierda/derecha).
const props = defineProps({ modelValue: { type: String, required: true }, pestanas: { type: Array, required: true } })
const emit = defineEmits(['update:modelValue'])

function mover(e, i) {
  const n = props.pestanas.length
  const j = e.key === 'ArrowRight' ? (i + 1) % n : e.key === 'ArrowLeft' ? (i - 1 + n) % n : null
  if (j === null) return
  e.preventDefault()
  emit('update:modelValue', props.pestanas[j].id)
  e.currentTarget.parentElement.children[j]?.focus()
}
</script>

<template>
  <div class="pestanas" role="tablist">
    <button v-for="(p, i) in pestanas" :key="p.id" type="button" role="tab" :aria-selected="modelValue === p.id"
            :tabindex="modelValue === p.id ? 0 : -1" :class="{ activa: modelValue === p.id }"
            @click="emit('update:modelValue', p.id)" @keydown="mover($event, i)">
      {{ p.nombre }}
      <span v-if="p.cuenta !== undefined && p.cuenta !== null" class="cuenta num">{{ p.cuenta }}</span>
    </button>
  </div>
</template>

<style scoped>
.pestanas { display: flex; gap: var(--e-1); border-bottom: 1px solid var(--linea); overflow-x: auto; }
button { display: inline-flex; align-items: center; gap: 6px; padding: 10px var(--e-3); border: 0; background: transparent; color: var(--tinta-3); font: inherit; font-weight: 550; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; white-space: nowrap; border-radius: 6px 6px 0 0; transition: color 0.15s, border-color 0.15s; }
button:hover { color: var(--tinta); }
button.activa { color: var(--acento-texto); border-bottom-color: var(--acento); }
.cuenta { font-size: 11.5px; min-width: 20px; height: 18px; padding: 0 6px; border-radius: 999px; background: var(--neutro-fondo); color: var(--tinta-2); display: inline-grid; place-items: center; }
.activa .cuenta { background: var(--acento-claro); color: var(--acento-texto); }
</style>
