<script setup>
// Ficha del producto: datos generales, características (según el tipo) y categorías.
// Se ve en modo lectura y se edita en el mismo lugar.
import { computed, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisar } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import { fecha, valorTexto } from '@/nucleo/formato.js'
import Campo from '@/componentes/Campo.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import SelectorCategorias from './SelectorCategorias.vue'

const props = defineProps({ producto: { type: Object, required: true }, esquema: { type: Object, required: true }, unidades: { type: Array, required: true } })
const emit = defineEmits(['actualizado', 'recargar'])
const editando = ref(null)
const errores = ref({})
const general = ref(null)
const guardando = ref(false)
const tipos = ref([])
catalogo('tipos-producto').then((t) => (tipos.value = t))

const campos = computed(() => props.esquema.campos.filter((c) => c.nivel === 'producto'))
const fuera = computed(() => Object.entries(props.producto.atributos_fuera_de_esquema || {}))

function editar() {
  errores.value = {}
  general.value = null
  const p = props.producto
  editando.value = { nombre: p.nombre, codigo: p.codigo, descripcion: p.descripcion || '', unidad_id: p.unidad.id,
    atributos: JSON.parse(JSON.stringify(p.atributos)), categorias: p.categorias.map((c) => c.id) }
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  general.value = null
  const e = editando.value
  // Todos los atributos del esquema: los vacíos se envían como null para quitarlos
  const atributos = Object.fromEntries(campos.value.map((c) => {
    const v = e.atributos[c.atributo.codigo]
    return [c.atributo.codigo, v === '' || (Array.isArray(v) && !v.length) ? null : v ?? null]
  }))
  try {
    const p = await api.patch(`/productos/${props.producto.id}`, { version: props.producto.version, nombre: e.nombre, codigo: e.codigo,
      descripcion: e.descripcion || null, unidad_id: e.unidad_id, atributos, categorias: e.categorias })
    emit('actualizado', p)
    editando.value = null
    avisar('Ficha guardada.')
  } catch (err) {
    errores.value = err.porCampo
    // Lo que exige el estado actual: se marca en cada campo además del aviso general
    for (const f of err.detalle?.faltantes || []) if (f.nivel === 'producto') errores.value[`atributos.${f.atributo}`] = 'Obligatorio en el estado actual.'
    general.value = err
    if (err.status === 409 && err.detalle?.version_actual) general.value = { message: 'Otra persona guardó cambios mientras usted editaba. Recargue la ficha para ver la versión actual (sus cambios no guardados se perderán).', recargar: true }
  } finally { guardando.value = false }
}

const grupos = computed(() => {
  // Atributos agrupados por su grupo (sección); sin grupo van primero
  const res = new Map()
  for (const c of campos.value) {
    const g = c.atributo.grupo_id ?? 0
    if (!res.has(g)) res.set(g, [])
    res.get(g).push(c)
  }
  return [...res.entries()]
})
const gruposAtributo = ref([])
catalogo('grupos-atributo').then((g) => (gruposAtributo.value = g))
const nombreGrupo = (id) => gruposAtributo.value.find((g) => g.id === id)?.nombre || 'Otros'
</script>

<template>
  <div class="ficha">
    <form v-if="editando" id="form-ficha" class="tarjeta" novalidate @submit.prevent="guardar">
      <header class="tarjeta-cabeza"><div><h2>Editar ficha</h2><p>Los cambios se guardan juntos.</p></div></header>
      <div class="tarjeta-cuerpo pila">
        <div v-if="general" class="aviso-caja error" role="alert"><Icono nombre="alerta" />
          <div>{{ general.message }}
            <ul v-if="general.detalle?.faltantes"><li v-for="(x, i) in general.detalle.faltantes" :key="i">{{ x.nombre }}</li></ul>
            <button v-if="general.recargar" class="btn chico" type="button" @click="editando = null; emit('recargar')">Recargar</button>
          </div>
        </div>
        <h3>Datos generales</h3>
        <div class="rejilla-2">
          <Campo etiqueta="Nombre" id="e-nombre" :error="errores.nombre" obligatorio><input id="e-nombre" v-model="editando.nombre" class="control" maxlength="200" /></Campo>
          <Campo etiqueta="Código" id="e-codigo" :error="errores.codigo" obligatorio ayuda="Cambiarlo no cambia los SKU de las variantes ya creadas.">
            <input id="e-codigo" v-model="editando.codigo" class="control mono" maxlength="60" /></Campo>
          <Campo etiqueta="Unidad base" id="e-unidad" :error="errores.unidad_id" obligatorio>
            <select id="e-unidad" v-model="editando.unidad_id" class="control">
              <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
            </select>
          </Campo>
        </div>
        <Campo etiqueta="Descripción" id="e-desc"><textarea id="e-desc" v-model="editando.descripcion" class="control" rows="3" /></Campo>
        <template v-if="campos.length">
          <h3>Características</h3>
          <div class="rejilla-2">
            <CampoAtributo v-for="c in campos" :key="c.atributo.id" v-model="editando.atributos[c.atributo.codigo]" :campo="c" :unidades="unidades"
                           :error="errores[`atributos.${c.atributo.codigo}`]" id-base="ficha" />
          </div>
        </template>
        <h3>Categorías</h3>
        <SelectorCategorias v-model="editando.categorias" />
      </div>
      <footer class="pie">
        <button class="btn" type="button" @click="editando = null">Cancelar</button>
        <button class="btn primario" type="submit" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar cambios</button>
      </footer>
    </form>

    <template v-else>
      <section class="tarjeta">
        <header class="tarjeta-cabeza">
          <h2>Características</h2>
          <button class="btn" type="button" @click="editar"><Icono nombre="editar" :tam="16" />Editar ficha</button>
        </header>
        <div class="tarjeta-cuerpo pila">
          <p v-if="producto.descripcion" class="descripcion">{{ producto.descripcion }}</p>
          <div v-for="[g, lista] in grupos" :key="g" class="grupo">
            <h3 v-if="grupos.length > 1 || g">{{ g ? nombreGrupo(g) : 'Generales' }}</h3>
            <dl class="datos">
              <div v-for="c in lista" :key="c.atributo.id">
                <dt>{{ c.atributo.nombre }}<span v-if="c.obligatorio" class="obligatorio" aria-label="obligatorio" /></dt>
                <dd :class="{ tenue: producto.atributos[c.atributo.codigo] === undefined }">
                  <template v-if="c.atributo.tipo_dato === 'opciones' && producto.atributos[c.atributo.codigo]">
                    <span v-for="v in producto.atributos[c.atributo.codigo]" :key="v" class="insignia sin-punto acento">{{ c.atributo.opciones.find((o) => o.codigo === v)?.nombre || v }}</span>
                  </template>
                  <RouterLink v-else-if="c.atributo.tipo_dato === 'referencia' && c.atributo.entidad_referencia === 'producto' && producto.atributos[c.atributo.codigo]"
                              :to="`/productos/${producto.atributos[c.atributo.codigo]}`">Producto #{{ producto.atributos[c.atributo.codigo] }}</RouterLink>
                  <template v-else>{{ producto.atributos[c.atributo.codigo] === undefined ? 'Sin dato' : valorTexto(producto.atributos[c.atributo.codigo], c.atributo) }}</template>
                </dd>
              </div>
            </dl>
          </div>
          <p v-if="!campos.length" class="tenue">El tipo {{ producto.tipo.nombre }} no tiene atributos del producto.
            <RouterLink :to="`/configuracion/tipos/${producto.tipo.id}`">Configurar el tipo</RouterLink></p>
          <div v-if="fuera.length" class="aviso-caja info">
            <Icono nombre="info" />
            <div>Valores que se conservan aunque el tipo ya no tenga esos atributos:
              <span v-for="[k, v] in fuera" :key="k" class="mono"> {{ k }} = {{ valorTexto(v) }};</span></div>
          </div>
        </div>
      </section>

      <aside class="pila">
        <section class="tarjeta">
          <header class="tarjeta-cabeza"><h2>Datos generales</h2></header>
          <dl class="datos una tarjeta-cuerpo">
            <div><dt>Código</dt><dd><code>{{ producto.codigo }}</code></dd></div>
            <div><dt>Tipo</dt><dd><RouterLink :to="`/configuracion/tipos/${producto.tipo.id}`">{{ esquema.ruta.map((c) => tipos.find((t) => t.codigo === c)?.nombre || c).join(' › ') }}</RouterLink></dd></div>
            <div><dt>Unidad base</dt><dd>{{ producto.unidad.nombre }} ({{ producto.unidad.codigo }})</dd></div>
            <div><dt>Creado</dt><dd>{{ fecha(producto.creado_en) }}</dd></div>
            <div><dt>Modificado</dt><dd>{{ fecha(producto.actualizado_en) }}</dd></div>
          </dl>
        </section>
        <section class="tarjeta">
          <header class="tarjeta-cabeza"><h2>Categorías</h2></header>
          <div class="tarjeta-cuerpo">
            <div v-if="producto.categorias.length" class="fila envolver">
              <span v-for="c in producto.categorias" :key="c.id" class="insignia sin-punto acento" :title="c.taxonomia">{{ c.nombre }}</span>
            </div>
            <p v-else class="tenue chico">Sin categorías.</p>
          </div>
        </section>
      </aside>
    </template>
  </div>
</template>

<style scoped>
.ficha { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: var(--e-5); align-items: start; padding-top: var(--e-2); }
.ficha > form { grid-column: 1 / -1; }
@media (max-width: 1000px) { .ficha { grid-template-columns: 1fr; } }
.descripcion { color: var(--tinta-2); white-space: pre-line; }
.grupo h3 { margin-bottom: var(--e-3); color: var(--tinta-2); }
.datos { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--e-4) var(--e-5); margin: 0; }
.datos.una { grid-template-columns: 1fr; gap: var(--e-3); }
.datos dt { font-size: 12.5px; color: var(--tinta-3); font-weight: 550; margin-bottom: 2px; }
.datos dd { margin: 0; font-weight: 500; display: flex; flex-wrap: wrap; gap: 4px; word-break: break-word; }
.pie { display: flex; justify-content: flex-end; gap: var(--e-2); padding: var(--e-4) var(--e-5); border-top: 1px solid var(--linea); background: var(--superficie-2); border-radius: 0 0 var(--radio-panel) var(--radio-panel); position: sticky; bottom: 0; }
h3 { color: var(--tinta-2); }
</style>
