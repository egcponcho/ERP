<script setup>
import Icono from './Icono.vue'

defineProps({ icono: { type: String, default: 'caja' }, titulo: { type: String, required: true }, texto: { type: String, default: '' } })
</script>

<template>
  <div class="vacio">
    <div class="circulo"><Icono :nombre="icono" :tam="22" /></div>
    <h3>{{ titulo }}</h3>
    <p v-if="texto" class="tenue">{{ texto }}</p>
    <div v-if="$slots.default" class="acciones"><slot /></div>
  </div>
</template>

<style scoped>
.vacio { display: flex; flex-direction: column; align-items: center; text-align: center; gap: var(--e-2); padding: var(--e-8) var(--e-5); }
.circulo { width: 48px; height: 48px; border-radius: 50%; display: grid; place-items: center; background: var(--acento-claro); color: var(--acento-texto); margin-bottom: var(--e-2); }
p { max-width: 46ch; font-size: 13.5px; }
.acciones { margin-top: var(--e-3); display: flex; gap: var(--e-2); }
</style>
