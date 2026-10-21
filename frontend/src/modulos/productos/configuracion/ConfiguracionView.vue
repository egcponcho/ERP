<script setup>
// Configuración del módulo: menú lateral de apartados (el mismo patrón de facturacion) y el apartado elegido.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Icono from '@/componentes/Icono.vue'
import { APARTADOS } from './catalogos.js'

const route = useRoute()
const actual = computed(() => route.meta.apartado || route.params.catalogo || route.path.split('/')[3])
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div><h1>Configuración de productos</h1>
        <p>Lo que define cómo son sus productos. Se configura una vez y el asistente de alta lo usa.</p></div>
      <div class="acciones"><RouterLink class="btn" to="/productos/nuevo"><Icono nombre="mas" :tam="16" />Nuevo producto</RouterLink></div>
    </header>
    <div class="layout-lateral">
      <nav class="menu-lateral" aria-label="Apartados de configuración">
        <template v-for="g in APARTADOS" :key="g.grupo">
          <p class="menu-grupo">{{ g.grupo }}</p>
          <RouterLink v-for="x in g.items" :key="x.ruta" :to="`/productos/configuracion/${x.ruta}`" class="menu-item"
                      :aria-current="actual === x.ruta ? 'page' : undefined"><Icono :nombre="x.icono" :tam="16" /><span class="menu-txt">{{ x.nombre }}</span></RouterLink>
        </template>
      </nav>
      <div class="layout-contenido"><RouterView :key="route.path" /></div>
    </div>
  </div>
</template>
