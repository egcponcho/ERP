<script setup>
// Pestañas de primer nivel (.pestanas) con flechas del teclado.
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
    <button v-for="(p, i) in pestanas" :key="p.id" type="button" role="tab" class="pestana" :aria-selected="modelValue === p.id"
            :tabindex="modelValue === p.id ? 0 : -1" @click="emit('update:modelValue', p.id)" @keydown="mover($event, i)">
      {{ p.nombre }}<span v-if="p.cuenta" class="cuenta" :class="{ alerta: p.alerta }">{{ p.cuenta }}</span>
    </button>
  </div>
</template>
