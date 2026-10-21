<script setup>
// Paso 3: las características que pide el tipo, agrupadas por sección.
import { computed, ref } from 'vue'
import { catalogo } from '@/nucleo/catalogos.js'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import { b } from './borrador.js'

const props = defineProps({ esquema: { type: Object, required: true },
                            datos: { type: Object, required: true }, errores: { type: Array, default: () => [] } })
const gruposAtributo = ref([])
catalogo('grupos-atributo').then((g) => (gruposAtributo.value = g)).catch(() => {})

const campos = computed(() => props.esquema.campos.filter((c) => c.nivel === 'producto'))
const grupos = computed(() => {
  const res = new Map()
  for (const c of campos.value) {
    const g = c.atributo.grupo_id ?? 0
    if (!res.has(g)) res.set(g, [])
    res.get(g).push(c)
  }
  return [...res.entries()].sort(([a], [b]) => (a === 0 ? -1 : b === 0 ? 1 : 0))
})
const nombreGrupo = (id) => gruposAtributo.value.find((g) => g.id === id)?.nombre || 'Otros datos'
const obligatorios = computed(() => campos.value.filter((c) => c.obligatorio))
const vacio = (v) => v === null || v === undefined || v === '' || (Array.isArray(v) && !v.length)
const completos = computed(() => obligatorios.value.filter((c) => !vacio(b.producto.atributos[c.atributo.codigo])).length)
const msj = (codigo) => props.errores.filter((e) => e.campo === `producto.atributos.${codigo}`).map((e) => e.mensaje.replace(/^[^:]+: /, '')).join(' ')
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>Características de {{ esquema.tipo.nombre.toLowerCase() }}</h2>
        <p>Los datos que el tipo pide para todos sus productos. Las marcadas con * son necesarias para activarlo.</p></div>
      <span v-if="obligatorios.length" class="etiqueta" :class="completos === obligatorios.length ? 'ok' : 'aviso'">{{ completos }} de {{ obligatorios.length }} obligatorias</span>
    </div>
    <template v-if="campos.length">
      <div v-for="[g, lista] in grupos" :key="g" class="grupo">
        <h3 v-if="grupos.length > 1" class="resumen-titulo">{{ g ? nombreGrupo(g) : 'Generales' }}</h3>
        <div class="rejilla-campos">
          <CampoAtributo v-for="c in lista" :key="c.atributo.id" v-model="b.producto.atributos[c.atributo.codigo]" :campo="c"
                         :unidades="datos.unidades" :error="msj(c.atributo.codigo)" id-base="asis" />
        </div>
      </div>
    </template>
    <div v-else class="nota info"><Icono nombre="info" :tam="16" />
      <span>El tipo {{ esquema.tipo.nombre }} no pide características del producto.
        {{ esquema.campos.some((c) => c.es_eje) ? 'Sus datos van en cada variante (paso siguiente).' : 'Puede continuar.' }}</span></div>
  </section>
</template>

<style scoped>
.grupo + .grupo { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--linea-suave); }
</style>
