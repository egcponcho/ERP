<script setup>
// Inicio general del ERP: una tarjeta por módulo activo. Cada módulo aporta la
// suya en su contrato (modulo.js → inicio); esta pantalla no conoce ninguno.
import { computed, defineAsyncComponent } from 'vue'
import { modulosActivos } from '@/nucleo/modulos.js'

const tarjetas = computed(() => modulosActivos.value.filter((m) => m.inicio)
  .map((m) => ({ clave: m.clave, componente: defineAsyncComponent(m.inicio) })))
const hoy = new Date().toLocaleDateString('es', { weekday: 'long', day: 'numeric', month: 'long' })
</script>

<template>
  <div>
    <header class="titulo-grande">
      <p class="sobretitulo">{{ hoy }}</p>
      <h1>Inicio</h1>
    </header>
    <div class="rejilla-inicio">
      <component :is="t.componente" v-for="t in tarjetas" :key="t.clave" />
    </div>
    <p v-if="!tarjetas.length" class="ayuda">No hay módulos activos. Revise la variable MODULOS del servidor.</p>
  </div>
</template>
