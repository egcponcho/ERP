<script setup>
// Resumen siempre a la vista mientras se arma el producto: qué lleva y qué falta.
import { computed } from 'vue'
import Icono from '@/componentes/Icono.vue'
import { b } from './borrador.js'

const props = defineProps({ esquema: { type: Object, default: null }, datos: { type: Object, required: true },
                            variantes: { type: Number, default: 0 }, faltan: { type: Number, default: 0 } })
const emit = defineEmits(['ir'])
const unidad = computed(() => props.datos.unidades.find((u) => u.id === b.producto.unidad_id))
const conEjes = computed(() => props.esquema?.campos.some((c) => c.es_eje))
const filas = computed(() => [
  { paso: 'tipo', icono: 'capas', texto: props.esquema?.tipo.nombre || 'Sin tipo', ok: !!props.esquema },
  { paso: 'general', icono: 'etiqueta', texto: b.producto.nombre || 'Sin nombre', sub: [b.producto.codigo || 'Código automático', unidad.value?.nombre].filter(Boolean).join(' · '), ok: !!b.producto.nombre.trim() },
  { paso: 'caracteristicas', icono: 'lista', texto: props.faltan ? `Faltan ${props.faltan} obligatorias` : 'Características completas', ok: !props.faltan },
  ...(conEjes.value ? [{ paso: 'variantes', icono: 'cuadricula', texto: props.variantes ? `${props.variantes} variantes` : 'Sin variantes elegidas', ok: props.variantes > 0 }] : []),
  { paso: 'empaque', icono: 'caja', texto: `${b.presentaciones.length} presentaciones · ${b.identificadores.length} códigos`, ok: null },
  { paso: 'clasificacion', icono: 'arbol', texto: `${b.producto.categorias.length} categorías`, ok: null },
])
</script>

<template>
  <aside class="panel resumen-alta" aria-label="Resumen del producto">
    <p class="resumen-titulo">Resumen</p>
    <ul class="resumen-lista">
      <li v-for="f in filas" :key="f.paso">
        <button type="button" class="ra-fila" @click="emit('ir', f.paso)">
          <Icono :nombre="f.icono" :tam="16" class="ra-icono" />
          <span class="crece"><span class="ra-texto">{{ f.texto }}</span><small v-if="f.sub" class="sub">{{ f.sub }}</small></span>
          <Icono v-if="f.ok === true" nombre="check" :tam="14" class="ra-ok" />
          <Icono v-else-if="f.ok === false" nombre="alerta" :tam="14" class="ra-falta" />
        </button>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
.resumen-alta { padding: 16px; }
.ra-fila { display: flex; align-items: center; gap: 10px; width: 100%; text-align: start; border: 0; background: none; padding: 6px; margin: 0 -6px; border-radius: var(--radio); cursor: pointer; font: inherit; color: inherit; }
.ra-fila:hover { background: var(--fila-hover); }
.ra-icono { color: var(--tinta-3); }
.ra-texto { font-size: 0.88rem; font-weight: 560; overflow-wrap: anywhere; }
.ra-ok { color: var(--ok); }
.ra-falta { color: var(--aviso); }
</style>
