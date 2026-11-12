<script setup>
// Tarjeta de Productos en el Inicio general: cifras clave, a dónde ir y lo
// último que se modificó. El detalle vive en el Resumen del módulo.
import { onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { claseEstado, fecha } from '@/modulos/productos/compartido/formato.js'
import Icono from '@/componentes/Icono.vue'

const r = ref(null)
onMounted(async () => {
  try { r.value = await api.get('/productos/resumen') } catch (e) { avisarError(e) }
})
const borradores = (x) => x.por_estado.filter((e) => e.inicial).reduce((s, e) => s + e.n, 0)
</script>

<template>
  <section class="panel tarjeta-modulo" aria-labelledby="inicio-productos">
    <RouterLink to="/productos" class="tarjeta-modulo-cabeza">
      <span class="icono-app"><Icono nombre="caja" :tam="20" /></span>
      <span class="crece"><h2 id="inicio-productos">Productos</h2><small>Catálogo, variantes, empaques y códigos</small></span>
      <Icono nombre="derecha" :tam="18" class="apagado" />
    </RouterLink>
    <dl v-if="r" class="cifras">
      <div><dt>Productos</dt><dd>{{ r.total }}</dd></div>
      <div><dt>Operables</dt><dd>{{ r.operables }}</dd></div>
      <div><dt>En borrador</dt><dd>{{ borradores(r) }}</dd></div>
      <div><dt>Variantes</dt><dd>{{ r.variantes }}</dd></div>
    </dl>
    <div v-else class="cifras" aria-busy="true"><span v-for="i in 4" :key="i" class="esqueleto" style="height: 52px" /></div>

    <template v-if="r?.recientes.length">
      <h3 class="titulo-grupo">Modificados hace poco</h3>
      <ul class="lista-accion">
        <li v-for="p in r.recientes.slice(0, 4)" :key="p.id">
          <RouterLink :to="`/productos/${p.id}`" class="lista-accion-fila">
            <span class="lista-accion-texto"><b>{{ p.nombre }}</b><small><span class="mono">{{ p.codigo }}</span> · {{ fecha(p.actualizado_en) }}</small></span>
            <span class="estado" :class="claseEstado({ operable: p.operable, codigo: p.estado })"><span class="estado-marca" />{{ p.estado_nombre }}</span>
          </RouterLink>
        </li>
      </ul>
    </template>
    <p v-else-if="r" class="ayuda">Todavía no hay productos. El asistente lo guía paso a paso.</p>

    <RouterLink to="/productos/nuevo" class="btn btn-primario"><Icono nombre="mas" :tam="16" />Nuevo producto</RouterLink>
  </section>
</template>
