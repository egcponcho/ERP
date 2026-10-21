<script setup>
// Módulo de productos: una sola entrada con tres apartados (catálogo, alta paso a
// paso y configuración). La ficha de un producto vive dentro del catálogo.
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const APARTADOS = [
  { a: '/productos', nombre: 'Catálogo', seccion: 'catalogo' },
  { a: '/productos/nuevo', nombre: 'Nuevo producto', seccion: 'nuevo' },
  { a: '/productos/configuracion', nombre: 'Configuración', seccion: 'configuracion' },
]
const actual = computed(() => route.meta.seccion)
</script>

<template>
  <div class="modulo">
    <nav class="pestanas-pildora modulo-nav" aria-label="Apartados de productos">
      <RouterLink v-for="x in APARTADOS" :key="x.a" :to="x.a" class="pildora" :aria-selected="actual === x.seccion"
                  :aria-current="actual === x.seccion ? 'page' : undefined">{{ x.nombre }}</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style scoped>
.modulo-nav { margin-bottom: 18px; }
</style>
