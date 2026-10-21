<script setup>
// Etiqueta + control + ayuda + error, con los atributos de accesibilidad enlazados.
defineProps({
  etiqueta: { type: String, required: true },
  id: { type: String, required: true },
  ayuda: { type: String, default: '' },
  error: { type: String, default: '' },
  obligatorio: { type: Boolean, default: false },
})
</script>

<template>
  <div class="campo">
    <label :for="id" :class="{ obligatorio }"><slot name="etiqueta">{{ etiqueta }}</slot></label>
    <slot />
    <p v-if="error" :id="`${id}-error`" class="error-campo" role="alert">{{ error }}</p>
    <p v-else-if="ayuda" :id="`${id}-ayuda`" class="ayuda">{{ ayuda }}</p>
  </div>
</template>
