<script setup>
// Tipos de producto en la tabla común, con su árbol (subtipos con sangría). El
// alta usa el mismo formulario que el asistente.
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import { camposDe, heredado, rutaTipo } from '@/nucleo/esquemaLocal.js'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'
import CreadorTipo from '../asistente/CreadorTipo.vue'

const router = useRouter()
const datos = reactive({ tipos: [], atributos: [], unidades: [], magnitudes: [] })
const cargando = ref(true)
const creando = ref(false)

onMounted(async () => {
  try {
    const [tipos, atributos, unidades, magnitudes] = await Promise.all([catalogo('tipos-producto', { recargar: true }), catalogo('atributos', { recargar: true }),
      catalogo('unidades'), catalogo('magnitudes')])
    Object.assign(datos, { tipos, atributos: [...atributos], unidades, magnitudes })
  } catch (e) { avisarError(e) } finally { cargando.value = false }
})

// Filas en orden de árbol, con su profundidad y lo que hereda
const filas = computed(() => {
  const hijos = {}
  for (const t of datos.tipos) (hijos[t.padre_id ?? 0] ||= []).push(t)
  const res = []
  const visitar = (padre, nivel) => {
    for (const t of (hijos[padre] || []).sort((a, b) => a.nombre.localeCompare(b.nombre))) {
      const campos = camposDe(t, datos.tipos, datos.atributos)
      res.push({ ...t, nivel, orden: res.length, ruta: rutaTipo(t, datos.tipos).map((x) => x.nombre).join(' › '),
        campos: campos.filter((c) => c.nivel === 'producto').length, ejes: campos.filter((c) => c.es_eje).map((c) => c.atributo.nombre),
        numeracion: heredado(t, datos.tipos, 'plantilla_codigo'), unidad: datos.unidades.find((u) => u.id === heredado(t, datos.tipos, 'unidad_defecto_id'))?.codigo })
      visitar(t.id, nivel + 1)
    }
  }
  visitar(0, 0)
  return res
})
const COLUMNAS = [
  { clave: 'nombre', texto: 'Tipo', fija: true, valor: (f) => f.ruta },
  { clave: 'campos', texto: 'Características', num: true, filtro: false },
  { clave: 'ejes', texto: 'Variantes por', valor: (f) => f.ejes },
  { clave: 'numeracion', texto: 'Numeración', filtro: false },
  { clave: 'unidad', texto: 'Unidad' },
  { clave: 'activo', texto: 'Activo', valor: (f) => f.activo, textoValor: (v) => (v ? 'Sí' : 'No') },
]
function creado(t) {
  invalidarCatalogo('tipos-producto')
  router.push(`/productos/configuracion/tipos/${t.id}`)
}
</script>

<template>
  <div>
    <div class="fila-flex entre seccion-cabeza">
      <div><h2>Tipos de producto</h2><p class="ayuda">Cada tipo define qué características tienen sus productos, cuáles distinguen variantes y cómo se numeran. Un subtipo hereda todo de su padre.</p></div>
      <button v-if="!creando" type="button" class="btn btn-primario" @click="creando = true"><Icono nombre="mas" :tam="16" />Nuevo tipo</button>
    </div>
    <CreadorTipo v-if="creando" :datos="datos" @cerrar="creando = false" @creado="creado" />
    <TablaDatos tabla="config-tipos" :columnas="COLUMNAS" :filas="filas" :cargando="cargando" orden-inicial="" fila-clicable etiqueta="Tipos de producto"
                @fila="(f) => router.push(`/productos/configuracion/tipos/${f.id}`)">
      <template #celda-nombre="{ fila }">
        <span class="arbol-nombre" :style="{ paddingInlineStart: `${fila.nivel * 22}px` }">
          <Icono v-if="fila.nivel" nombre="heredado" :tam="14" class="apagado" /><b>{{ fila.nombre }}</b><code class="apagado">{{ fila.codigo }}</code></span></template>
      <template #celda-ejes="{ fila }"><span v-if="fila.ejes.length" class="etiqueta acento ms-0">{{ fila.ejes.join(' × ') }}</span><span v-else class="apagado">Sin variantes</span></template>
      <template #celda-numeracion="{ fila }"><code v-if="fila.numeracion">{{ fila.numeracion }}</code><span v-else class="apagado">Manual</span></template>
      <template #celda-activo="{ fila }"><span class="estado" :class="fila.activo ? 'estado-ok' : 'estado-neutro'"><span class="estado-marca" />{{ fila.activo ? 'Activo' : 'Inactivo' }}</span></template>
      <template #acciones="{ fila }"><RouterLink class="btn btn-chico btn-fantasma" :to="`/productos/configuracion/tipos/${fila.id}`" @click.stop>Configurar<Icono nombre="derecha" :tam="14" /></RouterLink></template>
      <template #vacio>Todavía no hay tipos de producto. <button type="button" class="btn-texto" @click="creando = true">Crear el primero</button></template>
    </TablaDatos>
  </div>
</template>

<style scoped>
.seccion-cabeza { margin-bottom: 14px; align-items: flex-start; }
.arbol-nombre { display: inline-flex; align-items: center; gap: 8px; }
</style>
