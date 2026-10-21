<script setup>
// Portada de la configuración: cada apartado dice para qué sirve y cuántos
// registros tiene, agrupados en el orden en que conviene configurarlos.
import { onMounted, reactive } from 'vue'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Icono from '@/componentes/Icono.vue'
import { APARTADOS } from './catalogos.js'

const cuentas = reactive({})
onMounted(async () => {
  try {
    await Promise.all(APARTADOS.flatMap((g) => g.items).map(async (x) => { cuentas[x.ruta] = (await catalogo(x.fuente, { recargar: true })).length }))
  } catch (e) { avisarError(e) }
})
</script>

<template>
  <div class="config-portada">
    <section v-for="g in APARTADOS" :key="g.grupo" :aria-labelledby="`g-${g.grupo}`">
      <h2 :id="`g-${g.grupo}`" class="resumen-titulo">{{ g.grupo }}</h2>
      <div class="config-tarjetas">
        <RouterLink v-for="x in g.items" :key="x.ruta" :to="`/productos/configuracion/${x.ruta}`" class="config-tarjeta">
          <span class="config-icono"><Icono :nombre="x.icono" :tam="20" /></span>
          <span class="config-texto">
            <b>{{ x.nombre }}</b>
            <small>{{ x.texto }}</small>
          </span>
          <span class="config-cuenta" :class="{ vacia: cuentas[x.ruta] === 0 }">
            <template v-if="cuentas[x.ruta] === undefined"><span class="esqueleto" style="width: 28px; height: 14px" /></template>
            <template v-else-if="cuentas[x.ruta] === 0">Sin registros</template>
            <template v-else>{{ cuentas[x.ruta] }} {{ cuentas[x.ruta] === 1 ? 'registro' : 'registros' }}</template>
          </span>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.config-portada { display: flex; flex-direction: column; gap: 22px; }
.config-tarjetas { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; }
.config-tarjeta {
  display: grid; grid-template-columns: auto minmax(0, 1fr); grid-template-rows: auto auto; gap: 4px 14px; padding: 16px; color: inherit; text-decoration: none;
  background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio-panel); box-shadow: var(--sombra);
  transition: border-color var(--rapido), box-shadow var(--rapido);
}
.config-tarjeta:hover { border-color: var(--acento-medio); box-shadow: var(--sombra-media); }
.config-icono { grid-row: span 2; width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center; background: var(--acento-claro); color: var(--acento-texto); }
.config-texto { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.config-texto b { font-size: 0.98rem; }
.config-texto small { color: var(--tinta-3); font-size: 0.84rem; line-height: 1.45; }
.config-cuenta { font-size: 0.8rem; font-weight: 650; color: var(--tinta-2); font-variant-numeric: tabular-nums; }
.config-cuenta.vacia { color: var(--aviso); }
@media (max-width: 400px) { .config-tarjetas { grid-template-columns: minmax(0, 1fr); } }
</style>
