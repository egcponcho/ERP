<script setup>
// Módulo de productos: una sola entrada en el menú. Adentro, sus apartados
// (Resumen, Catálogo y Configuración) y «Nuevo producto» siempre a la vista.
// La ficha de un producto cuelga del catálogo.
import MarcoModulo from '@/componentes/MarcoModulo.vue'
import contrato from './modulo.js'
</script>

<template>
  <MarcoModulo :modulo="contrato"><RouterView /></MarcoModulo>
</template>
