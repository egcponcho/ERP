<script setup>
// Taxonomías (formas de agrupar) y el árbol de categorías de cada una.
import { computed, onMounted, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import TablaCatalogo from './TablaCatalogo.vue'

const taxonomias = ref(null)
const categorias = ref([])
const elegida = ref(null)
const editando = ref(null)
const errores = ref({})
const guardando = ref(false)

async function cargar() {
  try {
    ;[taxonomias.value, categorias.value] = await Promise.all([catalogo('taxonomias', { recargar: true }), catalogo('categorias', { recargar: true })])
    if (!taxonomias.value.some((t) => t.id === elegida.value)) elegida.value = taxonomias.value[0]?.id ?? null
  } catch (e) { avisarError(e); taxonomias.value = [] }
}
onMounted(cargar)

const taxonomia = computed(() => taxonomias.value?.find((t) => t.id === elegida.value))
const arbol = computed(() => {
  const hijos = {}
  for (const c of categorias.value.filter((c) => c.taxonomia_id === elegida.value)) (hijos[c.padre_id ?? 0] ||= []).push(c)
  const res = []
  const visitar = (padre, nivel) => {
    for (const c of (hijos[padre] || []).sort((a, b) => a.orden - b.orden || a.nombre.localeCompare(b.nombre))) {
      res.push({ ...c, nivel, hijos: (hijos[c.id] || []).length })
      visitar(c.id, nivel + 1)
    }
  }
  visitar(0, 0)
  return res
})
const contar = (taxId) => categorias.value.filter((c) => c.taxonomia_id === taxId).length

function abrir(c = null, padre = null) {
  errores.value = {}
  editando.value = c ? { ...c } : { taxonomia_id: elegida.value, padre_id: padre, codigo: '', nombre: '', orden: 0, activa: true }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  const { id, nivel: _n, hijos: _h, creado_en: _c, actualizado_en: _a, ...cuerpo } = editando.value
  try {
    if (id) await api.patch(`${CONFIG}/categorias/${id}`, cuerpo)
    else await api.post(`${CONFIG}/categorias`, cuerpo)
    avisar(id ? 'Categoría guardada.' : `Se creó la categoría ${cuerpo.nombre}.`)
    editando.value = null
    invalidarCatalogo('categorias')
    await cargar()
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { guardando.value = false }
}

async function borrar(c) {
  const ok = await confirmar({ titulo: 'Borrar categoría', mensaje: `Se borrará «${c.nombre}». Si tiene productos o subcategorías no se podrá borrar: desactívela.`, accion: 'Borrar', peligro: true })
  if (!ok) return
  try {
    await api.del(`${CONFIG}/categorias/${c.id}`)
    avisar('Categoría borrada.')
    invalidarCatalogo('categorias')
    await cargar()
  } catch (e) { avisarError(e) }
}

function codigoDesdeNombre() {
  if (editando.value.id || editando.value.codigoTocado) return
  editando.value.codigo = editando.value.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 30)
}
</script>

<template>
  <div class="pagina">
    <header class="pagina-cabeza">
      <div>
        <div class="migas">Configuración</div>
        <h1>Categorías</h1>
        <p>Agrupe sus productos de varias formas a la vez: cada taxonomía es un árbol independiente (línea comercial, familia contable, canal de venta…).</p>
      </div>
    </header>

    <div class="dos">
      <section class="tarjeta lista-tax">
        <header class="tarjeta-cabeza"><h2>Taxonomías</h2></header>
        <nav v-if="taxonomias?.length" aria-label="Taxonomías">
          <button v-for="t in taxonomias" :key="t.id" type="button" class="tax" :class="{ activa: t.id === elegida }"
                  :aria-current="t.id === elegida ? 'true' : undefined" @click="elegida = t.id">
            <span class="crece"><strong>{{ t.nombre }}</strong>
              <span class="tenue chico">{{ t.multiple ? 'Varias por producto' : 'Una por producto' }}{{ t.obligatoria ? ' · obligatoria' : '' }}</span></span>
            <span class="insignia sin-punto num">{{ contar(t.id) }}</span>
          </button>
        </nav>
        <p v-else-if="taxonomias" class="tenue chico vacio">Cree una taxonomía en la tabla de abajo.</p>
      </section>

      <section class="tarjeta">
        <header class="tarjeta-cabeza">
          <div><h2>{{ taxonomia ? taxonomia.nombre : 'Categorías' }}</h2><p v-if="taxonomia">Árbol de categorías de esta taxonomía.</p></div>
          <button class="btn primario" type="button" :disabled="!taxonomia" @click="abrir()"><Icono nombre="mas" :tam="16" />Nueva categoría</button>
        </header>
        <ul v-if="arbol.length" class="arbol" role="tree" :aria-label="taxonomia?.nombre">
          <li v-for="c in arbol" :key="c.id" role="treeitem" :aria-level="c.nivel + 1" class="nodo" :style="{ paddingLeft: `${20 + c.nivel * 24}px` }">
            <Icono v-if="c.hijos" nombre="abajo" :tam="14" class="tenue" />
            <span v-else class="hoja" aria-hidden="true" />
            <span class="crece"><strong :class="{ tenue: !c.activa }">{{ c.nombre }}</strong> <code class="tenue">{{ c.codigo }}</code>
              <span v-if="!c.activa" class="insignia">Inactiva</span></span>
            <button class="btn fantasma chico" type="button" @click="abrir(null, c.id)"><Icono nombre="mas" :tam="14" />Subcategoría</button>
            <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${c.nombre}`" @click="abrir(c)"><Icono nombre="editar" :tam="16" /></button>
            <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Borrar ${c.nombre}`" @click="borrar(c)"><Icono nombre="borrar" :tam="16" /></button>
          </li>
        </ul>
        <EstadoVacio v-else-if="taxonomia" icono="arbol" :titulo="`${taxonomia.nombre} no tiene categorías`" texto="Agregue la primera; después podrá anidar subcategorías.">
          <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Nueva categoría</button>
        </EstadoVacio>
        <EstadoVacio v-else-if="taxonomias" icono="arbol" titulo="Primero cree una taxonomía" texto="Por ejemplo «Línea comercial» o «Familia contable»." />
      </section>
    </div>

    <TablaCatalogo ruta="taxonomias" @cambio="cargar" />

    <Modal v-if="editando" :titulo="editando.id ? 'Editar categoría' : 'Nueva categoría'" :descripcion="taxonomia?.nombre" @cerrar="editando = null">
      <form id="form-categoria" class="pila" @submit.prevent="guardar">
        <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
        <div class="rejilla-2">
          <Campo etiqueta="Nombre" id="c-nombre" :error="errores.nombre" obligatorio>
            <input id="c-nombre" v-model="editando.nombre" class="control" required maxlength="100" @input="codigoDesdeNombre" />
          </Campo>
          <Campo etiqueta="Código" id="c-codigo" :error="errores.codigo" obligatorio>
            <input id="c-codigo" v-model="editando.codigo" class="control mono" required maxlength="30" @input="editando.codigoTocado = true" />
          </Campo>
        </div>
        <Campo etiqueta="Dentro de" id="c-padre" :error="errores.padre_id">
          <select id="c-padre" v-model="editando.padre_id" class="control">
            <option :value="null">Nivel principal</option>
            <option v-for="c in arbol.filter((x) => x.id !== editando.id)" :key="c.id" :value="c.id">{{ '— '.repeat(c.nivel) }}{{ c.nombre }}</option>
          </select>
        </Campo>
        <div class="rejilla-2">
          <Campo etiqueta="Orden" id="c-orden"><input id="c-orden" v-model.number="editando.orden" class="control num" type="number" /></Campo>
          <label class="interruptor alinear"><input v-model="editando.activa" type="checkbox" />Activa</label>
        </div>
      </form>
      <template #pie>
        <button class="btn" type="button" @click="editando = null">Cancelar</button>
        <button class="btn primario" type="submit" form="form-categoria" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.dos { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: var(--e-5); align-items: start; }
@media (max-width: 900px) { .dos { grid-template-columns: 1fr; } }
.lista-tax nav { display: flex; flex-direction: column; padding: var(--e-2); gap: 2px; }
.tax { display: flex; align-items: center; gap: var(--e-3); text-align: left; padding: 10px var(--e-3); border: 0; background: transparent; border-radius: var(--radio); cursor: pointer; font: inherit; color: var(--tinta); transition: background-color 0.15s; }
.tax:hover { background: var(--fila-hover); }
.tax.activa { background: var(--acento-claro); }
.tax.activa strong { color: var(--acento-texto); }
.tax strong { display: block; font-weight: 600; }
.vacio { padding: var(--e-4); }
.arbol { list-style: none; margin: 0; padding: var(--e-2) 0; }
.nodo { display: flex; align-items: center; gap: var(--e-2); padding-top: 6px; padding-bottom: 6px; padding-right: var(--e-4); border-bottom: 1px solid var(--linea-suave); }
.nodo:last-child { border-bottom: 0; }
.nodo:hover { background: var(--fila-hover); }
.hoja { width: 14px; display: grid; place-items: center; }
.hoja::before { content: ''; width: 5px; height: 5px; border-radius: 50%; background: var(--borde-control); }
.alinear { align-self: end; height: var(--alto-control); }
</style>
