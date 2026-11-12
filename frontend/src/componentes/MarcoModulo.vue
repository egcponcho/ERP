<script setup>
// Marco común de un módulo: título grande, sus apartados en un control
// segmentado y su acción principal siempre a la vista. Recibe el contrato del
// módulo (modulo.js) y deja el contenido en el slot.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Icono from './Icono.vue'

const props = defineProps({ modulo: { type: Object, required: true } })
const route = useRoute()
const actual = computed(() => route.meta.seccion)
const conAccion = computed(() => props.modulo.accion && route.path !== props.modulo.accion.a)
</script>

<template>
  <div class="modulo">
    <div class="modulo-barra">
      <nav class="segmentos modulo-apartados" :aria-label="`Apartados de ${modulo.nombre.toLowerCase()}`">
        <RouterLink v-for="x in modulo.apartados" :key="x.a" :to="x.a" class="segmento"
                    :aria-current="actual === x.seccion ? (route.path === x.a ? 'page' : 'true') : undefined">{{ x.nombre }}</RouterLink>
      </nav>
      <RouterLink v-if="conAccion" class="btn btn-primario modulo-accion" :to="modulo.accion.a" :aria-label="modulo.accion.texto" :title="modulo.accion.texto">
        <Icono :nombre="modulo.accion.icono || 'mas'" :tam="17" /><span class="modulo-accion-texto">{{ modulo.accion.texto }}</span></RouterLink>
    </div>
    <slot />
  </div>
</template>
