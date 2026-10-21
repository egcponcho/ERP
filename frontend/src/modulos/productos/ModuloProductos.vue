<script setup>
// Módulo de productos: una sola entrada en el menú. Adentro, sus pestañas
// (Resumen, Catálogo y Configuración) y su acción principal, «Nuevo producto»,
// siempre a la vista. La ficha de un producto cuelga del catálogo.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Icono from '@/componentes/Icono.vue'

const route = useRoute()
const APARTADOS = [
  { a: '/productos', nombre: 'Resumen', seccion: 'resumen' },
  { a: '/productos/catalogo', nombre: 'Catálogo', seccion: 'catalogo' },
  { a: '/productos/configuracion', nombre: 'Configuración', seccion: 'configuracion' },
]
const actual = computed(() => route.meta.seccion)
</script>

<template>
  <div class="modulo">
    <div class="modulo-barra">
      <nav class="pestanas" aria-label="Apartados de productos">
        <RouterLink v-for="x in APARTADOS" :key="x.a" :to="x.a" class="pestana" :aria-current="actual === x.seccion ? (route.path === x.a ? 'page' : 'true') : undefined">{{ x.nombre }}</RouterLink>
      </nav>
      <div v-if="actual !== 'nuevo'" class="modulo-barra-accion">
        <RouterLink class="btn btn-primario" to="/productos/nuevo"><Icono nombre="mas" :tam="16" />Nuevo producto</RouterLink>
      </div>
    </div>
    <RouterView />
  </div>
</template>
