<script setup>
import { computed } from 'vue'
import { PAGINAS } from './catalogos.js'
import TablaCatalogo from './TablaCatalogo.vue'

const props = defineProps({ catalogo: { type: String, required: true } })
const pagina = computed(() => PAGINAS[props.catalogo])
</script>

<template>
  <div class="pagina">
    <template v-if="pagina">
      <header class="pagina-cabeza">
        <div>
          <div class="migas">Configuración</div>
          <h1>{{ pagina.titulo }}</h1>
          <p>{{ pagina.descripcion }}</p>
        </div>
      </header>
      <TablaCatalogo v-for="c in pagina.catalogos" :key="c" :ruta="c" />
    </template>
    <p v-else class="tenue">Esta sección no existe.</p>
  </div>
</template>
