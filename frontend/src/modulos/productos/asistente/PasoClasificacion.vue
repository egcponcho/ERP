<script setup>
// Paso: en qué categorías aparece el producto (una por taxonomía, o varias si la taxonomía lo permite).
import SelectorCategorias from '@/componentes/SelectorCategorias.vue'
import { b } from './borrador.js'

defineProps({ errores: { type: Array, default: () => [] } })
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza"><div><h2>Categorías</h2><p>Dónde se agrupa el producto: línea comercial, familia contable, canal de venta… Las marcadas con * son necesarias para activarlo.</p></div></div>
    <div v-if="errores.length" class="nota error mb-3" role="alert"><ul class="lista-mensajes"><li v-for="(e, i) in errores" :key="i">{{ e.mensaje }}</li></ul></div>
    <SelectorCategorias v-model="b.producto.categorias" />
  </section>
</template>
