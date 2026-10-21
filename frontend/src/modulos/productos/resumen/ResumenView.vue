<script setup>
// Tablero del módulo de productos: cómo está el catálogo (cifras, productos por
// estado y por tipo), qué falta por completar y lo último que se modificó. Cada
// cifra lleva al catálogo con su filtro puesto. Mientras falte configuración,
// la puesta en marcha va primero y dice qué sigue.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { claseEstado, fecha } from '@/nucleo/formato.js'
import Icono from '@/componentes/Icono.vue'

const r = ref(null) // GET /productos/resumen
const conf = ref(null)
const error = ref(false)

async function cargar() {
  error.value = false
  try {
    const [resumen, tipos, unidades, estados, categorias] = await Promise.all([api.get('/productos/resumen'),
      catalogo('tipos-producto', { recargar: true }), catalogo('unidades', { recargar: true }), catalogo('estados', { recargar: true }),
      catalogo('categorias', { recargar: true })])
    r.value = resumen
    conf.value = { tipos, unidades, estados, categorias }
  } catch (e) {
    error.value = true
    avisarError(e)
  }
}
onMounted(cargar)

const catalogoCon = (query) => ({ path: '/productos/catalogo', query })
const codigos = (filtro) => (r.value?.por_estado || []).filter(filtro).map((e) => e.codigo)

// ---- Puesta en marcha --------------------------------------------------------------------
const pasos = computed(() => {
  const c = conf.value
  if (!c) return []
  return [
    { hecho: c.unidades.length > 0 && c.estados.length > 0, titulo: 'Unidades y estados', texto: 'En qué se miden los productos y su ciclo de vida (Borrador, Activo…).', a: '/productos/configuracion/unidades' },
    { hecho: c.tipos.some((t) => t.atributos > 0), titulo: 'Tipos de producto y sus características', texto: 'Uno por rubro: calzado, químicos, alimentos… También se crean desde el asistente.', a: '/productos/configuracion/tipos' },
    { hecho: c.categorias.length > 0, titulo: 'Categorías', texto: 'Opcional: línea comercial, familia contable, canal de venta…', a: '/productos/configuracion/categorias', opcional: true },
    { hecho: r.value.total > 0, titulo: 'Primer producto', texto: 'El asistente lo guía paso a paso.', a: '/productos/nuevo' },
  ]
})
const pendientesConfig = computed(() => pasos.value.filter((p) => !p.hecho && !p.opcional).length)
const avance = computed(() => pasos.value.filter((p) => p.hecho).length)

// ---- Cifras -----------------------------------------------------------------------------
const borradores = computed(() => (r.value?.por_estado || []).filter((e) => e.inicial).reduce((s, e) => s + e.n, 0))
const kpis = computed(() => {
  const x = r.value
  return [
    { rotulo: 'Productos', icono: 'caja', cifra: x.total, pie: `${x.por_tipo.length} ${x.por_tipo.length === 1 ? 'tipo' : 'tipos'} de producto`, a: catalogoCon({}) },
    { rotulo: 'Operables', icono: 'check', cifra: x.operables, pie: 'Listos para compras, ventas e inventario', a: catalogoCon({ estado: codigos((e) => e.operable) }) },
    { rotulo: 'En borrador', icono: 'editar', cifra: borradores.value, pie: 'Por completar y activar', a: catalogoCon({ estado: codigos((e) => e.inicial) }) },
    { rotulo: 'Variantes (SKU)', icono: 'capas', cifra: x.variantes, pie: `${x.presentaciones} ${x.presentaciones === 1 ? 'presentación' : 'presentaciones'}`, a: catalogoCon({}) },
  ]
})

// ---- Barras ----------------------------------------------------------------------------------
const MAX_TIPOS = 8
const maximo = (lista) => Math.max(1, ...lista.map((x) => x.n))
const porEstado = computed(() => r.value.por_estado)
const porTipo = computed(() => r.value.por_tipo.slice(0, MAX_TIPOS))
const otrosTipos = computed(() => r.value.por_tipo.slice(MAX_TIPOS).reduce((s, x) => s + x.n, 0))
const ancho = (n, lista) => `${(n / maximo(lista)) * 100}%`
const porcentaje = (n) => (r.value.total ? `${Math.round((n / r.value.total) * 100)} % del catálogo` : '')

// ---- Por completar -------------------------------------------------------------------------
const pendientes = computed(() => {
  const p = r.value.pendientes
  return [
    { n: borradores.value, titulo: 'En borrador', texto: 'Complete su ficha y páselos a un estado operable.', a: catalogoCon({ estado: codigos((e) => e.inicial) }) },
    { n: p.sin_codigos, titulo: 'Sin códigos', texto: 'Sin código de barras ni otros códigos alternos.', a: catalogoCon({ pendiente: 'sin_codigos' }) },
    { n: p.sin_presentaciones, titulo: 'Sin presentaciones', texto: 'Sin empaques de venta o compra (caja, bulto, tambor…).', a: catalogoCon({ pendiente: 'sin_presentaciones' }) },
    ...(conf.value.categorias.length ? [{ n: p.sin_categorias, titulo: 'Sin categoría', texto: 'No están en ninguna categoría.', a: catalogoCon({ pendiente: 'sin_categorias' }) }] : []),
  ]
})
const todoCompleto = computed(() => pendientes.value.every((p) => !p.n))
</script>

<template>
  <div>
    <header class="pagina-cabeza">
      <div>
        <h1>Resumen de productos</h1>
        <p>Cómo está su catálogo y qué falta por completar. Cada cifra abre el catálogo con ese filtro.</p>
      </div>
    </header>

    <div v-if="error" class="nota error" role="alert">
      <Icono nombre="alerta" :tam="16" /><span class="crece">No se pudo cargar el resumen.</span>
      <button type="button" class="btn btn-chico" @click="cargar">Reintentar</button>
    </div>

    <!-- Cargando: el mismo esqueleto que ocupará el tablero (sin saltos) -->
    <div v-else-if="!r" aria-busy="true" aria-label="Cargando el resumen">
      <div class="kpis"><div v-for="i in 4" :key="i" class="kpi"><span class="esqueleto" style="width: 90px; height: 14px" /><span class="esqueleto" style="width: 60px; height: 30px" /></div></div>
      <div class="dos-columnas mt"><div class="panel"><span class="esqueleto" style="height: 160px" /></div><div class="panel"><span class="esqueleto" style="height: 160px" /></div></div>
    </div>

    <template v-else>
      <!-- Puesta en marcha: primero, mientras falte algo indispensable -->
      <section v-if="pendientesConfig || !r.total" class="panel mb-3" aria-labelledby="t-marcha">
        <div class="panel-cabeza">
          <div><h2 id="t-marcha">Puesta en marcha</h2><p>{{ avance }} de {{ pasos.length }} pasos. Siga el orden: cada paso usa lo del anterior.</p></div>
          <div class="avance" style="width: 180px"><div class="avance-riel"><div class="avance-relleno" :class="{ completo: avance === pasos.length }" :style="{ width: `${(avance / pasos.length) * 100}%` }" /></div></div>
        </div>
        <ol class="lista-accion">
          <li v-for="(p, i) in pasos" :key="p.titulo">
            <RouterLink :to="p.a" class="lista-accion-fila">
              <span class="cifra-tono" :class="{ 'tono-info': !p.hecho }"><Icono v-if="p.hecho" nombre="check" :tam="16" /><template v-else>{{ i + 1 }}</template></span>
              <span class="lista-accion-texto"><b>{{ p.titulo }}<span v-if="p.hecho" class="oculto-visual"> (hecho)</span></b><small>{{ p.texto }}</small></span>
              <span class="lista-accion-boton">{{ p.hecho ? 'Revisar' : 'Empezar' }}<Icono nombre="derecha" :tam="14" /></span>
            </RouterLink>
          </li>
        </ol>
      </section>

      <template v-if="r.total">
        <section class="kpis" aria-label="Cifras del catálogo">
          <RouterLink v-for="k in kpis" :key="k.rotulo" :to="k.a" class="kpi">
            <span class="kpi-rotulo"><Icono :nombre="k.icono" :tam="15" />{{ k.rotulo }}</span>
            <span class="kpi-cifra">{{ k.cifra.toLocaleString('es') }}</span>
            <span class="kpi-pie">{{ k.pie }}</span>
          </RouterLink>
        </section>

        <div class="dos-columnas mt">
          <section class="panel" aria-labelledby="t-estado">
            <div class="panel-cabeza"><div><h2 id="t-estado">Productos por estado</h2><p>En qué parte de su ciclo de vida están.</p></div></div>
            <ul class="barras">
              <li v-for="e in porEstado" :key="e.codigo">
                <RouterLink :to="catalogoCon({ estado: [e.codigo] })" class="barra-fila" :title="porcentaje(e.n)">
                  <span class="barra-rotulo"><span class="estado" :class="claseEstado(e)"><span class="estado-marca" />{{ e.nombre }}</span></span>
                  <span class="barra-riel" aria-hidden="true"><span class="barra-dato" :style="{ width: ancho(e.n, porEstado)}" /></span>
                  <span class="barra-cifra">{{ e.n }}</span>
                </RouterLink>
              </li>
            </ul>
          </section>

          <section class="panel" aria-labelledby="t-tipo">
            <div class="panel-cabeza">
              <div><h2 id="t-tipo">Productos por tipo</h2><p>Los tipos con más productos.</p></div>
              <RouterLink to="/productos/configuracion/tipos" class="btn btn-chico btn-fantasma">Ver tipos</RouterLink>
            </div>
            <ul class="barras">
              <li v-for="t in porTipo" :key="t.codigo">
                <RouterLink :to="catalogoCon({ tipo: [t.codigo] })" class="barra-fila" :title="porcentaje(t.n)">
                  <span class="barra-rotulo"><span>{{ t.nombre }}</span></span>
                  <span class="barra-riel" aria-hidden="true"><span class="barra-dato" :style="{ width: ancho(t.n, porTipo)}" /></span>
                  <span class="barra-cifra">{{ t.n }}</span>
                </RouterLink>
              </li>
              <li v-if="otrosTipos" class="barra-fila"><span class="barra-rotulo apagado">Otros tipos</span><span /><span class="barra-cifra">{{ otrosTipos }}</span></li>
            </ul>
          </section>
        </div>

        <div class="dos-columnas mt">
          <section class="panel" aria-labelledby="t-completar">
            <div class="panel-cabeza"><div><h2 id="t-completar">Por completar</h2>
              <p>{{ todoCompleto ? 'Nada pendiente: todos los productos tienen lo básico.' : 'Productos a los que les falta algo. Abra la lista y complételos.' }}</p></div></div>
            <ul class="lista-accion">
              <li v-for="p in pendientes" :key="p.titulo">
                <RouterLink v-if="p.n" :to="p.a" class="lista-accion-fila">
                  <span class="cifra-tono tono-alerta">{{ p.n }}</span>
                  <span class="lista-accion-texto"><b>{{ p.titulo }}</b><small>{{ p.texto }}</small></span>
                  <span class="lista-accion-boton">Ver<Icono nombre="derecha" :tam="14" /></span>
                </RouterLink>
                <div v-else class="lista-accion-fila">
                  <span class="cifra-tono" aria-hidden="true"><Icono nombre="check" :tam="16" /></span>
                  <span class="lista-accion-texto"><b>{{ p.titulo }}: ninguno</b><small>{{ p.texto }}</small></span>
                </div>
              </li>
            </ul>
          </section>

          <section class="panel" aria-labelledby="t-recientes">
            <div class="panel-cabeza"><div><h2 id="t-recientes">Modificados recientemente</h2></div>
              <RouterLink to="/productos/catalogo" class="btn btn-chico btn-fantasma">Ver catálogo</RouterLink></div>
            <ul class="lista-accion">
              <li v-for="p in r.recientes" :key="p.id">
                <RouterLink :to="`/productos/${p.id}`" class="lista-accion-fila">
                  <span class="lista-accion-texto"><b>{{ p.nombre }}</b><small><span class="mono">{{ p.codigo }}</span> · {{ p.tipo_nombre }} · {{ fecha(p.actualizado_en) }}</small></span>
                  <span class="estado" :class="claseEstado({ operable: p.operable, codigo: p.estado })"><span class="estado-marca" />{{ p.estado_nombre }}</span>
                </RouterLink>
              </li>
            </ul>
          </section>
        </div>
      </template>

    </template>
  </div>
</template>
