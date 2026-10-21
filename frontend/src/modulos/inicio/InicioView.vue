<script setup>
// Inicio: cifras del catálogo y una guía de configuración paso a paso.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Icono from '@/componentes/Icono.vue'

const datos = ref(null)

onMounted(async () => {
  try {
    const [productos, tipos, atributos, unidades, estados, categorias, recientes] = await Promise.all([
      api.get('/productos', { tamano: 1 }), catalogo('tipos-producto', { recargar: true }), catalogo('atributos', { recargar: true }),
      catalogo('unidades'), catalogo('estados', { recargar: true }), catalogo('categorias', { recargar: true }),
      api.get('/productos', { tamano: 6, orden: '-actualizado' })])
    datos.value = { productos: productos.total, tipos, atributos, unidades, estados, categorias, recientes: recientes.datos }
  } catch (e) { avisarError(e); datos.value = { productos: 0, tipos: [], atributos: [], unidades: [], estados: [], categorias: [], recientes: [] } }
})

const pasos = computed(() => {
  const d = datos.value
  if (!d) return []
  return [
    { hecho: d.unidades.length > 0 && d.estados.length > 0, titulo: 'Unidades y estados', texto: 'Las unidades de medida y el ciclo de vida de los productos.', a: '/configuracion/unidades' },
    { hecho: d.atributos.length > 0, titulo: 'Atributos', texto: 'Las características de sus productos: color, talla, peso, pureza…', a: '/configuracion/atributos' },
    { hecho: d.tipos.some((t) => t.atributos > 0), titulo: 'Tipos de producto', texto: 'Un tipo por rubro, con sus atributos y sus ejes de variante.', a: '/configuracion/tipos' },
    { hecho: d.categorias.length > 0, titulo: 'Categorías (opcional)', texto: 'Árboles para agrupar: línea comercial, familia contable…', a: '/configuracion/categorias' },
    { hecho: d.productos > 0, titulo: 'Primer producto', texto: 'Cree un producto: el formulario se arma solo según su tipo.', a: '/productos' },
  ]
})
const avance = computed(() => pasos.value.filter((p) => p.hecho).length)
const estado = (codigo) => datos.value?.estados.find((e) => e.codigo === codigo)
</script>

<template>
  <div class="pagina">
    <header class="pagina-cabeza">
      <div>
        <h1>Catálogo de productos</h1>
        <p>Un solo modelo para cualquier rubro: lo particular de cada producto se configura, no se programa.</p>
      </div>
      <RouterLink class="btn primario" to="/productos?nuevo=1"><Icono nombre="mas" :tam="16" />Nuevo producto</RouterLink>
    </header>

    <section class="cifras" aria-label="Resumen">
      <RouterLink v-for="c in [
        { n: 'Productos', v: datos?.productos, i: 'caja', a: '/productos' },
        { n: 'Tipos de producto', v: datos?.tipos.length, i: 'capas', a: '/configuracion/tipos' },
        { n: 'Atributos', v: datos?.atributos.length, i: 'etiqueta', a: '/configuracion/atributos' },
        { n: 'Categorías', v: datos?.categorias.length, i: 'arbol', a: '/configuracion/categorias' },
      ]" :key="c.n" :to="c.a" class="cifra tarjeta">
        <span class="icono-cifra"><Icono :nombre="c.i" /></span>
        <span><span class="tenue chico">{{ c.n }}</span>
          <strong class="num"><template v-if="datos">{{ c.v }}</template><span v-else class="esqueleto" style="width: 40px; height: 22px" /></strong></span>
      </RouterLink>
    </section>

    <div class="dos">
      <section class="tarjeta">
        <header class="tarjeta-cabeza">
          <div><h2>Puesta en marcha</h2><p>{{ avance }} de {{ pasos.length }} pasos completos</p></div>
          <div class="barra" role="progressbar" :aria-valuenow="avance" aria-valuemin="0" :aria-valuemax="pasos.length" aria-label="Avance de la configuración">
            <span :style="{ width: `${pasos.length ? (avance / pasos.length) * 100 : 0}%` }" />
          </div>
        </header>
        <ol class="pasos">
          <li v-for="(p, i) in pasos" :key="p.titulo" :class="{ hecho: p.hecho }">
            <span class="marca-paso" aria-hidden="true"><Icono v-if="p.hecho" nombre="check" :tam="14" /><template v-else>{{ i + 1 }}</template></span>
            <span class="crece"><strong>{{ p.titulo }}</strong><span class="tenue chico">{{ p.texto }}</span></span>
            <RouterLink class="btn chico" :class="{ fantasma: p.hecho }" :to="p.a">{{ p.hecho ? 'Ver' : 'Configurar' }}<Icono nombre="flecha" :tam="14" /></RouterLink>
          </li>
        </ol>
      </section>

      <section class="tarjeta">
        <header class="tarjeta-cabeza"><div><h2>Modificados recientemente</h2></div><RouterLink to="/productos" class="chico">Ver todos</RouterLink></header>
        <ul v-if="datos?.recientes.length" class="recientes">
          <li v-for="p in datos.recientes" :key="p.id">
            <RouterLink :to="`/productos/${p.id}`">
              <span class="crece"><strong>{{ p.nombre }}</strong><code class="tenue">{{ p.codigo }}</code></span>
              <span class="insignia" :class="estado(p.estado)?.operable ? 'ok' : 'info'">{{ estado(p.estado)?.nombre || p.estado }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-else-if="datos" class="tenue chico vacio">Todavía no hay productos.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.cifras { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--e-4); }
.cifra { display: flex; align-items: center; gap: var(--e-4); padding: var(--e-4) var(--e-5); color: var(--tinta); transition: border-color 0.15s, box-shadow 0.15s; }
.cifra:hover { text-decoration: none; border-color: var(--acento); box-shadow: var(--sombra-media); }
.cifra strong { display: block; font-size: 24px; font-weight: 650; line-height: 1.2; }
.icono-cifra { width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center; background: var(--acento-claro); color: var(--acento-texto); }
.dos { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: var(--e-5); align-items: start; }
@media (max-width: 1000px) { .dos { grid-template-columns: 1fr; } }
.barra { width: 140px; height: 8px; border-radius: 999px; background: var(--neutro-fondo); overflow: hidden; }
.barra span { display: block; height: 100%; background: var(--acento); border-radius: 999px; transition: width 0.3s; }
.pasos { list-style: none; margin: 0; padding: var(--e-2) 0; }
.pasos li { display: flex; align-items: center; gap: var(--e-4); padding: var(--e-3) var(--e-5); }
.pasos strong { display: block; font-weight: 600; }
.marca-paso { width: 28px; height: 28px; border-radius: 50%; flex: none; display: grid; place-items: center; font-size: 13px; font-weight: 600; border: 1.5px solid var(--borde-control); color: var(--tinta-3); }
.hecho .marca-paso { background: var(--ok); border-color: var(--ok); color: #fff; }
.hecho strong { color: var(--tinta-2); }
.recientes { list-style: none; margin: 0; padding: var(--e-2); }
.recientes a { display: flex; align-items: center; gap: var(--e-3); padding: 10px var(--e-3); border-radius: var(--radio); color: var(--tinta); }
.recientes a:hover { background: var(--fila-hover); text-decoration: none; }
.recientes strong { display: block; font-weight: 550; }
.vacio { padding: var(--e-5); }
</style>
