<script setup>
import { computed } from 'vue'
import Icono from './Icono.vue'

const props = defineProps({ pagina: { type: Number, required: true }, tamano: { type: Number, required: true }, total: { type: Number, required: true } })
const emit = defineEmits(['cambiar'])
const paginas = computed(() => Math.max(1, Math.ceil(props.total / props.tamano)))
const desde = computed(() => (props.total ? (props.pagina - 1) * props.tamano + 1 : 0))
const hasta = computed(() => Math.min(props.total, props.pagina * props.tamano))
</script>

<template>
  <nav class="paginacion" aria-label="Paginación">
    <span class="tenue chico num">{{ desde }}–{{ hasta }} de {{ total }}</span>
    <div class="fila">
      <button class="btn chico icono" type="button" :disabled="pagina <= 1" aria-label="Página anterior" @click="emit('cambiar', pagina - 1)"><Icono nombre="izquierda" :tam="16" /></button>
      <span class="chico num">Página {{ pagina }} de {{ paginas }}</span>
      <button class="btn chico icono" type="button" :disabled="pagina >= paginas" aria-label="Página siguiente" @click="emit('cambiar', pagina + 1)"><Icono nombre="derecha" :tam="16" /></button>
    </div>
  </nav>
</template>

<style scoped>
.paginacion { display: flex; justify-content: space-between; align-items: center; padding: var(--e-3) var(--e-4); border-top: 1px solid var(--linea); gap: var(--e-3); }
</style>
