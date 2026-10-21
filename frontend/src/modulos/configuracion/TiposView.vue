<script setup>
// Tipos de producto: el árbol de rubros (Calzado → Calzado deportivo…).
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import FilasEsqueleto from '@/componentes/FilasEsqueleto.vue'
import Icono from '@/componentes/Icono.vue'
import FormTipo from './FormTipo.vue'

const router = useRouter()
const tipos = ref(null)
const unidades = ref([])
const creando = ref(null)

// El árbol aplanado en orden, con su profundidad
const arbol = computed(() => {
  const hijos = {}
  for (const t of tipos.value || []) (hijos[t.padre_id ?? 0] ||= []).push(t)
  const res = []
  const visitar = (padre, nivel) => {
    for (const t of (hijos[padre] || []).sort((a, b) => a.nombre.localeCompare(b.nombre))) {
      res.push({ ...t, nivel })
      visitar(t.id, nivel + 1)
    }
  }
  visitar(0, 0)
  return res
})

async function cargar() {
  try {
    ;[tipos.value, unidades.value] = await Promise.all([catalogo('tipos-producto', { recargar: true }), catalogo('unidades')])
  } catch (e) { avisarError(e); tipos.value = [] }
}
onMounted(cargar)

function nuevo(padre = null) {
  creando.value = { codigo: '', nombre: '', descripcion: '', padre_id: padre, unidad_defecto_id: null, plantilla_codigo: '', siguiente_numero: 1, plantilla_sku: '', activo: true }
}

async function crear(datos) {
  try {
    const t = await api.post(`${CONFIG}/tipos-producto`, datos)
    invalidarCatalogo('tipos-producto')
    avisar(`Se creó el tipo ${t.nombre}. Ahora asígnele sus atributos.`)
    router.push(`/configuracion/tipos/${t.id}`)
  } catch (e) { return e }
}

const unidad = (id) => unidades.value.find((u) => u.id === id)?.codigo
</script>

<template>
  <div class="pagina">
    <header class="pagina-cabeza">
      <div>
        <div class="migas">Configuración</div>
        <h1>Tipos de producto</h1>
        <p>Cada tipo define qué atributos tienen sus productos, cuáles distinguen variantes y cómo se numeran. Un subtipo hereda todo de su padre.</p>
      </div>
      <button class="btn primario" type="button" @click="nuevo()"><Icono nombre="mas" :tam="16" />Nuevo tipo</button>
    </header>

    <section class="tarjeta">
      <div class="tabla-envoltura">
        <table class="tabla">
          <thead><tr><th>Tipo</th><th>Atributos propios</th><th>Unidad</th><th>Numeración</th><th>SKU de variantes</th><th>Estado</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
          <tbody>
            <FilasEsqueleto v-if="tipos === null" :columnas="7" :filas="4" />
            <tr v-for="t in arbol" :key="t.id" class="clicable" @click="router.push(`/configuracion/tipos/${t.id}`)">
              <td>
                <div class="nombre" :style="{ paddingLeft: `${t.nivel * 22}px` }">
                  <Icono v-if="t.nivel" nombre="heredado" :tam="14" class="tenue" />
                  <RouterLink :to="`/configuracion/tipos/${t.id}`" @click.stop>{{ t.nombre }}</RouterLink>
                  <code class="tenue">{{ t.codigo }}</code>
                </div>
              </td>
              <td class="num">{{ t.atributos }}</td>
              <td>{{ unidad(t.unidad_defecto_id) || (t.padre_id ? 'Heredada' : '—') }}</td>
              <td><code v-if="t.plantilla_codigo">{{ t.plantilla_codigo }}</code><span v-else class="tenue">{{ t.padre_id ? 'Heredada' : 'Manual' }}</span></td>
              <td><code v-if="t.plantilla_sku">{{ t.plantilla_sku }}</code><span v-else class="tenue">{{ t.padre_id ? 'Heredado' : 'Automático' }}</span></td>
              <td><span class="insignia" :class="t.activo ? 'ok' : ''">{{ t.activo ? 'Activo' : 'Inactivo' }}</span></td>
              <td class="acciones" @click.stop>
                <button class="btn fantasma chico" type="button" :aria-label="`Nuevo subtipo de ${t.nombre}`" @click="nuevo(t.id)"><Icono nombre="mas" :tam="14" />Subtipo</button>
              </td>
            </tr>
          </tbody>
        </table>
        <EstadoVacio v-if="tipos && !tipos.length" icono="capas" titulo="Aún no hay tipos de producto"
                     texto="Cree un tipo por cada rubro que maneja (calzado, químicos, alimentos…) y asígnele sus atributos.">
          <button class="btn primario" type="button" @click="nuevo()"><Icono nombre="mas" :tam="16" />Nuevo tipo</button>
        </EstadoVacio>
      </div>
    </section>

    <FormTipo v-if="creando" :datos="creando" :tipos="tipos || []" :unidades="unidades" titulo="Nuevo tipo de producto"
              :guardar="crear" @cerrar="creando = null" />
  </div>
</template>

<style scoped>
.nombre { display: flex; align-items: center; gap: var(--e-2); font-weight: 550; }
.nombre a { color: var(--tinta); }
</style>
