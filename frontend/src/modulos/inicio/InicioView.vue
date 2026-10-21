<script setup>
// Inicio general del ERP: una tarjeta por módulo con sus cifras clave y a dónde ir,
// y la actividad reciente. El detalle de cada módulo vive en su propio tablero.
import { onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { claseEstado, fecha } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'

const productos = ref(null)

onMounted(async () => {
  try { productos.value = await api.get('/productos/resumen') } catch (e) { avisarError(e) }
})
const borradores = (r) => r.por_estado.filter((e) => e.inicial).reduce((s, e) => s + e.n, 0)
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div><h1>Inicio</h1><p>Sus módulos y lo último que se movió. Cada módulo tiene su propio resumen.</p></div>
    </header>

    <div class="dos-columnas">
      <section class="panel modulo-tarjeta" aria-labelledby="m-productos">
        <div class="modulo-tarjeta-cabeza">
          <span class="modulo-icono"><Icono nombre="caja" :tam="22" /></span>
          <div><h2 id="m-productos">Productos</h2><p class="ayuda">Catálogo de cualquier rubro: tipos, características, variantes, empaques y códigos.</p></div>
        </div>
        <dl v-if="productos" class="cifras">
          <div><dt>Productos</dt><dd>{{ productos.total }}</dd></div>
          <div><dt>Operables</dt><dd>{{ productos.operables }}</dd></div>
          <div><dt>En borrador</dt><dd>{{ borradores(productos) }}</dd></div>
          <div><dt>Variantes</dt><dd>{{ productos.variantes }}</dd></div>
        </dl>
        <div v-else class="cifras" aria-busy="true"><span v-for="i in 4" :key="i" class="esqueleto" style="height: 44px" /></div>
        <div class="fila-flex">
          <RouterLink to="/productos" class="btn">Abrir Productos<Icono nombre="derecha" :tam="15" /></RouterLink>
          <RouterLink to="/productos/nuevo" class="btn btn-fantasma"><Icono nombre="mas" :tam="15" />Nuevo producto</RouterLink>
        </div>
      </section>

      <section class="panel" aria-labelledby="t-actividad">
        <div class="panel-cabeza"><h2 id="t-actividad">Actividad reciente</h2></div>
        <ul v-if="productos?.recientes.length" class="lista-accion">
          <li v-for="p in productos.recientes" :key="p.id">
            <RouterLink :to="`/productos/${p.id}`" class="lista-accion-fila">
              <span class="lista-accion-texto"><b>{{ p.nombre }}</b><small>Producto <span class="mono">{{ p.codigo }}</span> · {{ fecha(p.actualizado_en) }}</small></span>
              <span class="estado" :class="claseEstado({ operable: p.operable, codigo: p.estado })"><span class="estado-marca" />{{ p.estado_nombre }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-else-if="productos" class="ayuda">Todavía no hay movimientos. Empiece por <RouterLink to="/productos">Productos</RouterLink>.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.modulo-tarjeta { display: flex; flex-direction: column; gap: 18px; }
.modulo-tarjeta-cabeza { display: flex; gap: 14px; align-items: flex-start; }
.modulo-tarjeta-cabeza h2 { font-size: 1.15rem; margin-bottom: 2px; }
.modulo-icono { width: 44px; height: 44px; border-radius: 10px; display: grid; place-items: center; background: var(--acento-claro); color: var(--acento-texto); flex: none; }
.cifras { grid-template-columns: repeat(4, minmax(0, 1fr)); }
@media (max-width: 600px) { .cifras { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
