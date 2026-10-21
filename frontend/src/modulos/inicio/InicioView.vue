<script setup>
// Inicio: cifras del catálogo, la puesta en marcha paso a paso y lo último que se modificó.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { fecha } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'

const datos = ref(null)

onMounted(async () => {
  try {
    const [productos, tipos, atributos, unidades, estados, categorias, recientes] = await Promise.all([
      api.get('/productos', { tamano: 1 }), catalogo('tipos-producto', { recargar: true }), catalogo('atributos', { recargar: true }),
      catalogo('unidades'), catalogo('estados', { recargar: true }), catalogo('categorias', { recargar: true }),
      api.get('/productos', { tamano: 6, orden: 'actualizado:desc' })])
    datos.value = { productos: productos.total, tipos, atributos, unidades, estados, categorias, recientes: recientes.datos }
  } catch (e) {
    avisarError(e)
    datos.value = { productos: 0, tipos: [], atributos: [], unidades: [], estados: [], categorias: [], recientes: [] }
  }
})

const pasos = computed(() => {
  const d = datos.value
  if (!d) return []
  return [
    { hecho: d.unidades.length > 0 && d.estados.length > 0, titulo: 'Unidades y estados', texto: 'En qué se miden los productos y su ciclo de vida.', a: '/productos/configuracion/unidades' },
    { hecho: d.tipos.some((t) => t.atributos > 0), titulo: 'Tipos de producto y sus características', texto: 'Un tipo por rubro: calzado, químicos, alimentos… (también se crean desde el asistente).', a: '/productos/configuracion/tipos' },
    { hecho: d.categorias.length > 0, titulo: 'Categorías (opcional)', texto: 'Línea comercial, familia contable, canal de venta…', a: '/productos/configuracion/categorias' },
    { hecho: d.productos > 0, titulo: 'Primer producto', texto: 'El asistente lo guía paso a paso.', a: '/productos/nuevo' },
  ]
})
const avance = computed(() => pasos.value.filter((p) => p.hecho).length)
const cifras = computed(() => [
  { n: 'Productos', v: datos.value?.productos, a: '/productos' },
  { n: 'Tipos de producto', v: datos.value?.tipos.length, a: '/productos/configuracion/tipos' },
  { n: 'Características', v: datos.value?.atributos.length, a: '/productos/configuracion/atributos' },
  { n: 'Categorías', v: datos.value?.categorias.length, a: '/productos/configuracion/categorias' },
])
const tono = (p) => (p.operable ? 'estado-ok' : p.estado === 'BORRADOR' ? 'estado-info' : 'estado-neutro')
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div><h1>Catálogo de productos</h1><p>Un solo modelo para cualquier rubro: lo particular de cada producto se configura, no se programa.</p></div>
      <div class="acciones"><RouterLink class="btn btn-primario" to="/productos/nuevo"><Icono nombre="mas" :tam="16" />Nuevo producto</RouterLink></div>
    </header>

    <section class="pl-cifras cifras-inicio" aria-label="Resumen">
      <RouterLink v-for="c in cifras" :key="c.n" :to="c.a" class="pl-cifra">
        <span>{{ c.n }}</span><b><template v-if="datos">{{ c.v }}</template><span v-else class="esqueleto" style="width: 40px; height: 22px" /></b>
      </RouterLink>
    </section>

    <div class="dos-columnas mt">
      <section class="panel">
        <div class="panel-cabeza">
          <div><h2>Puesta en marcha</h2><p>{{ avance }} de {{ pasos.length }} pasos</p></div>
          <div class="avance"><div class="avance-riel"><div class="avance-relleno" :class="{ completo: avance === pasos.length }" :style="{ width: `${pasos.length ? (avance / pasos.length) * 100 : 0}%` }" /></div></div>
        </div>
        <ul class="lista-accion">
          <li v-for="(p, i) in pasos" :key="p.titulo">
            <RouterLink :to="p.a" class="lista-accion-fila">
              <span class="cifra-tono" :class="p.hecho ? '' : 'tono-info'"><Icono v-if="p.hecho" nombre="check" :tam="16" /><template v-else>{{ i + 1 }}</template></span>
              <span class="lista-accion-texto"><b>{{ p.titulo }}</b><small>{{ p.texto }}</small></span>
              <span class="lista-accion-boton">{{ p.hecho ? 'Ver' : 'Empezar' }}<Icono nombre="derecha" :tam="14" /></span>
            </RouterLink>
          </li>
        </ul>
      </section>

      <section class="panel">
        <div class="panel-cabeza"><h2>Modificados recientemente</h2><RouterLink to="/productos" class="btn btn-chico btn-fantasma">Ver catálogo</RouterLink></div>
        <ul v-if="datos?.recientes.length" class="lista-accion">
          <li v-for="p in datos.recientes" :key="p.id">
            <RouterLink :to="`/productos/${p.id}`" class="lista-accion-fila">
              <span class="lista-accion-texto"><b>{{ p.nombre }}</b><small><span class="mono">{{ p.codigo }}</span> · {{ p.tipo_nombre }} · {{ fecha(p.actualizado_en) }}</small></span>
              <span class="estado" :class="tono(p)"><span class="estado-marca" />{{ p.estado_nombre }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-else-if="datos" class="ayuda">Todavía no hay productos. <RouterLink to="/productos/nuevo">Crear el primero</RouterLink></p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.cifras-inicio { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.cifras-inicio .pl-cifra { text-decoration: none; padding: 16px 18px; transition: background 0.12s; }
.cifras-inicio .pl-cifra:hover { background: var(--fila-hover); }
.cifras-inicio .pl-cifra > b { font-size: 1.6rem; }
@media (max-width: 720px) { .cifras-inicio { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
