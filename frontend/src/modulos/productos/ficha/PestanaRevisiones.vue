<script setup>
// Revisiones publicadas en la tabla común; cada fila se abre para ver qué cambió
// respecto de la anterior y la ficha congelada.
import { onMounted, reactive, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { fecha, valorTexto } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ producto: { type: Object, required: true } })
const emit = defineEmits(['publicar'])
const lista = ref([])
const cargando = ref(true)
const detalle = reactive({}) // numero → { revision, cambios }
const COLUMNAS = [
  { clave: 'numero', texto: 'Revisión', num: true, fija: true },
  { clave: 'vigencia', texto: 'Vigencia', filtro: false, valor: (f) => f.vigente_desde },
  { clave: 'estado', texto: 'Estado', valor: (f) => (f.vigente_hasta ? 'Cerrada' : 'Vigente') },
  { clave: 'motivo', texto: 'Motivo', filtro: false },
]

onMounted(async () => {
  try { lista.value = await api.get(`/productos/${props.producto.id}/revisiones`) } catch (e) { avisarError(e) } finally { cargando.value = false }
})

async function abrir(r) {
  if (detalle[r.numero]) return
  try {
    const actual = await api.get(`/productos/${props.producto.id}/revisiones/${r.numero}`)
    const anterior = r.numero > 1 ? await api.get(`/productos/${props.producto.id}/revisiones/${r.numero - 1}`) : null
    const cambios = []
    if (anterior) {
      const a = anterior.datos
      const b = actual.datos
      for (const k of ['codigo', 'nombre', 'descripcion']) if (a[k] !== b[k]) cambios.push({ campo: k, antes: a[k], despues: b[k] })
      for (const k of new Set([...Object.keys(a.atributos), ...Object.keys(b.atributos)])) {
        if (JSON.stringify(a.atributos[k]) !== JSON.stringify(b.atributos[k])) cambios.push({ campo: k, antes: valorTexto(a.atributos[k]), despues: valorTexto(b.atributos[k]) })
      }
      if (a.variantes.length !== b.variantes.length) cambios.push({ campo: 'variantes', antes: a.variantes.length, despues: b.variantes.length })
    }
    detalle[r.numero] = { revision: actual, cambios, primera: !anterior }
  } catch (e) { avisarError(e) }
}
</script>

<template>
  <div>
    <div class="fila-flex mb-3">
      <p class="ayuda crece">Cada revisión congela la ficha completa con su vigencia y ya no cambia. Abra una para ver qué cambió.</p>
      <button type="button" class="btn btn-primario" @click="emit('publicar')"><Icono nombre="publicar" :tam="16" />Publicar revisión</button>
    </div>
    <TablaDatos tabla="revisiones" :columnas="COLUMNAS" :filas="lista" clave-fila="numero" :cargando="cargando" expandible orden-inicial="numero:desc"
                etiqueta="Revisiones" @expandir="abrir">
      <template #celda-vigencia="{ fila }">{{ fecha(fila.vigente_desde) }}<span v-if="fila.vigente_hasta" class="sub">hasta {{ fecha(fila.vigente_hasta) }}</span></template>
      <template #celda-estado="{ fila }"><span class="estado" :class="fila.vigente_hasta ? 'estado-neutro' : 'estado-ok'"><span class="estado-marca" />{{ fila.vigente_hasta ? 'Cerrada' : 'Vigente' }}</span></template>
      <template #celda-motivo="{ fila }"><span class="envolver">{{ fila.motivo || '—' }}</span></template>
      <template #detalle="{ fila }">
        <template v-if="detalle[fila.numero]">
          <p v-if="detalle[fila.numero].primera" class="ayuda">Primera revisión publicada.</p>
          <table v-else-if="detalle[fila.numero].cambios.length" class="pl-tabla">
            <thead><tr><th>Dato</th><th>Antes</th><th>Después</th></tr></thead>
            <tbody><tr v-for="c in detalle[fila.numero].cambios" :key="c.campo"><td><code>{{ c.campo }}</code></td>
              <td class="antes">{{ c.antes ?? '—' }}</td><td class="despues">{{ c.despues ?? '—' }}</td></tr></tbody>
          </table>
          <p v-else class="ayuda">Sin cambios en los datos ni en las características respecto de la revisión anterior.</p>
          <dl class="resumen-datos mt-chico">
            <dt>Nombre</dt><dd>{{ detalle[fila.numero].revision.datos.nombre }}</dd>
            <dt>Estado</dt><dd>{{ detalle[fila.numero].revision.datos.estado.nombre }}</dd>
            <dt>Variantes</dt><dd>{{ detalle[fila.numero].revision.datos.variantes.length }}</dd>
          </dl>
        </template>
        <span v-else class="esqueleto" style="height: 40px" />
      </template>
      <template #vacio>Todavía no hay revisiones. Publique una cuando la ficha esté lista: queda una copia fija con fecha, útil para auditorías y cambios de receta.</template>
    </TablaDatos>
  </div>
</template>

<style scoped>
.antes { color: var(--error); text-decoration: line-through; }
.despues { color: var(--ok); font-weight: 600; }
</style>
