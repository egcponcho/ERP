<script setup>
// Atributos: las características que pueden tener los productos de cualquier rubro.
import { computed, onMounted, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import { TIPOS_DATO } from '@/nucleo/formato.js'
import Campo from '@/componentes/Campo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import FilasEsqueleto from '@/componentes/FilasEsqueleto.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import TablaCatalogo from './TablaCatalogo.vue'

const atributos = ref(null)
const magnitudes = ref([])
const unidades = ref([])
const grupos = ref([])
const entidades = ref([])
const busqueda = ref('')
const filtroTipo = ref('')
const editando = ref(null)
const errores = ref({})
const guardando = ref(false)

const AYUDA_TIPO = {
  texto: 'Nombre, número CAS, temporada…', entero: 'Vida útil en días, garantía en meses…', decimal: 'Pureza, peso, voltaje, con o sin unidad…',
  booleano: 'Peligroso, apto para veganos…', fecha: 'Vencimiento, lanzamiento…', opcion: 'Color, talla, material: una de una lista',
  opciones: 'Alérgenos, certificaciones: varias de una lista', referencia: 'Apunta a otro registro (un producto base, una marca…)',
}
const REGLAS = {
  texto: [{ k: 'longitud_min', n: 'Largo mínimo' }, { k: 'longitud_max', n: 'Largo máximo' }, { k: 'patron', n: 'Formato (expresión regular)', texto: true }],
  entero: [{ k: 'minimo', n: 'Mínimo' }, { k: 'maximo', n: 'Máximo' }],
  decimal: [{ k: 'minimo', n: 'Mínimo' }, { k: 'maximo', n: 'Máximo' }, { k: 'decimales', n: 'Decimales permitidos' }],
  fecha: [{ k: 'minimo', n: 'Desde', fecha: true }, { k: 'maximo', n: 'Hasta', fecha: true }],
  opciones: [{ k: 'minimo', n: 'Elegir al menos' }, { k: 'maximo', n: 'Elegir como máximo' }],
}

const visibles = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return (atributos.value || []).filter((a) => (!filtroTipo.value || a.tipo_dato === filtroTipo.value)
    && (!q || `${a.codigo} ${a.nombre}`.toLowerCase().includes(q)))
})
const e = computed(() => editando.value?.datos)
const esNumero = computed(() => ['entero', 'decimal'].includes(e.value?.tipo_dato))
const conOpciones = computed(() => ['opcion', 'opciones'].includes(e.value?.tipo_dato))
const unidadesMagnitud = computed(() => unidades.value.filter((u) => u.magnitud_id === e.value?.magnitud_id))

async function cargar() {
  try {
    ;[atributos.value, magnitudes.value, unidades.value, grupos.value, entidades.value] = await Promise.all([
      catalogo('atributos', { recargar: true }), catalogo('magnitudes'), catalogo('unidades'), catalogo('grupos-atributo', { recargar: true }),
      api.get(`${CONFIG}/entidades-referenciables`)])
  } catch (err) { avisarError(err); atributos.value = [] }
}
onMounted(cargar)

function abrir(a = null) {
  errores.value = {}
  editando.value = {
    id: a?.id ?? null,
    usado: false,
    datos: a ? { ...a, reglas: { ...a.reglas }, opciones: a.opciones.map((o) => ({ ...o })) }
      : { codigo: '', nombre: '', descripcion: '', tipo_dato: 'texto', magnitud_id: null, unidad_defecto_id: null, entidad_referencia: null,
          reglas: {}, grupo_id: null, orden: 0, activo: true, opciones: [] },
    opcionesOriginales: a ? a.opciones.map((o) => ({ ...o })) : [],
  }
}

function codigoDesdeNombre() {
  if (editando.value.id || editando.value.codigoTocado) return
  e.value.codigo = e.value.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').replace(/^(\d)/, 'a_$1').slice(0, 40)
}

function agregarOpcion() {
  e.value.opciones.push({ codigo: '', nombre: '', orden: e.value.opciones.length + 1, activa: true, nueva: true })
}
function codigoOpcion(o) {
  if (o.nueva && !o.codigoTocado) o.codigo = o.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 40)
}

function reglasLimpias() {
  const res = {}
  for (const r of REGLAS[e.value.tipo_dato] || []) {
    const v = e.value.reglas[r.k]
    if (v === '' || v === null || v === undefined) continue
    res[r.k] = r.texto || r.fecha ? v : Number(v)
  }
  return res
}

async function guardar() {
  guardando.value = true
  errores.value = {}
  const d = e.value
  const cuerpo = {
    codigo: d.codigo, nombre: d.nombre, descripcion: d.descripcion || null, tipo_dato: d.tipo_dato,
    magnitud_id: esNumero.value ? d.magnitud_id : null, unidad_defecto_id: esNumero.value && d.magnitud_id ? d.unidad_defecto_id : null,
    entidad_referencia: d.tipo_dato === 'referencia' ? d.entidad_referencia : null, reglas: reglasLimpias(),
    grupo_id: d.grupo_id, orden: Number(d.orden) || 0, activo: d.activo,
  }
  const opciones = conOpciones.value ? d.opciones.filter((o) => o.nombre.trim()) : []
  try {
    if (!editando.value.id) {
      await api.post(`${CONFIG}/atributos`, { ...cuerpo, opciones: opciones.map(({ codigo, nombre, orden, activa }) => ({ codigo, nombre, orden: Number(orden) || 0, activa })) })
    } else {
      const id = editando.value.id
      await api.patch(`${CONFIG}/atributos/${id}`, cuerpo)
      for (const o of opciones) {
        const datos = { codigo: o.codigo, nombre: o.nombre, orden: Number(o.orden) || 0, activa: o.activa }
        if (o.nueva) await api.post(`${CONFIG}/atributos/${id}/opciones`, datos)
        else {
          const antes = editando.value.opcionesOriginales.find((x) => x.id === o.id)
          if (JSON.stringify({ ...antes, ...datos }) !== JSON.stringify(antes)) await api.patch(`${CONFIG}/atributos/${id}/opciones/${o.id}`, datos)
        }
      }
      for (const o of editando.value.opcionesOriginales) {
        if (!opciones.some((x) => x.id === o.id)) await api.del(`${CONFIG}/atributos/${id}/opciones/${o.id}`)
      }
    }
    avisar(editando.value.id ? 'Atributo guardado.' : `Se creó el atributo ${d.nombre}.`)
    editando.value = null
    invalidarCatalogo('atributos')
    await cargar()
  } catch (err) {
    errores.value = err.porCampo
    avisarError(err)
  } finally { guardando.value = false }
}

async function borrar(a) {
  const ok = await confirmar({ titulo: 'Borrar atributo', mensaje: `Se borrará «${a.nombre}». Si algún tipo o producto lo usa, no se podrá borrar: desactívelo en su lugar.`, accion: 'Borrar', peligro: true })
  if (!ok) return
  try {
    await api.del(`${CONFIG}/atributos/${a.id}`)
    avisar('Atributo borrado.')
    invalidarCatalogo('atributos')
    await cargar()
  } catch (err) { avisarError(err) }
}

const nombreGrupo = (id) => grupos.value.find((g) => g.id === id)?.nombre
const nombreMagnitud = (id) => magnitudes.value.find((m) => m.id === id)?.nombre
</script>

<template>
  <div class="pagina">
    <header class="pagina-cabeza">
      <div>
        <div class="migas">Configuración</div>
        <h1>Atributos</h1>
        <p>Las características que puede tener un producto. Se definen una vez y se asignan a los tipos de producto que las usan.</p>
      </div>
      <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Nuevo atributo</button>
    </header>

    <section class="tarjeta">
      <div class="filtros">
        <div class="busqueda crece">
          <Icono nombre="buscar" :tam="16" />
          <input v-model="busqueda" class="control" type="search" aria-label="Buscar atributos" placeholder="Buscar por código o nombre" />
        </div>
        <select v-model="filtroTipo" class="control tipo-filtro" aria-label="Filtrar por tipo de dato">
          <option value="">Todos los tipos de dato</option>
          <option v-for="(n, k) in TIPOS_DATO" :key="k" :value="k">{{ n }}</option>
        </select>
      </div>
      <div class="tabla-envoltura">
        <table class="tabla">
          <thead><tr><th>Atributo</th><th>Tipo de dato</th><th>Detalle</th><th>Grupo</th><th>Estado</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
          <tbody>
            <FilasEsqueleto v-if="atributos === null" :columnas="6" />
            <tr v-for="a in visibles" :key="a.id" class="clicable" @click="abrir(a)">
              <td><div class="nombre">{{ a.nombre }}</div><code class="tenue">{{ a.codigo }}</code></td>
              <td><span class="insignia sin-punto info">{{ TIPOS_DATO[a.tipo_dato] }}</span></td>
              <td class="tenue chico">
                <template v-if="a.opciones.length">{{ a.opciones.slice(0, 4).map((o) => o.nombre).join(', ') }}<template v-if="a.opciones.length > 4"> y {{ a.opciones.length - 4 }} más</template></template>
                <template v-else-if="a.magnitud_id">{{ nombreMagnitud(a.magnitud_id) }}<template v-if="a.unidad_defecto"> · {{ a.unidad_defecto }}</template></template>
                <template v-else-if="a.entidad_referencia">→ {{ a.entidad_referencia }}</template>
                <template v-else>—</template>
              </td>
              <td>{{ nombreGrupo(a.grupo_id) || '—' }}</td>
              <td><span class="insignia" :class="a.activo ? 'ok' : ''">{{ a.activo ? 'Activo' : 'Inactivo' }}</span></td>
              <td class="acciones" @click.stop>
                <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${a.nombre}`" @click="abrir(a)"><Icono nombre="editar" :tam="16" /></button>
                <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Borrar ${a.nombre}`" @click="borrar(a)"><Icono nombre="borrar" :tam="16" /></button>
              </td>
            </tr>
          </tbody>
        </table>
        <EstadoVacio v-if="atributos && !atributos.length" icono="etiqueta" titulo="Aún no hay atributos"
                     texto="Cree las características que describen sus productos: color, talla, peso, pureza, vida útil…">
          <button class="btn primario" type="button" @click="abrir()"><Icono nombre="mas" :tam="16" />Nuevo atributo</button>
        </EstadoVacio>
        <p v-else-if="atributos && !visibles.length" class="tenue sin-resultados">Ningún atributo coincide con el filtro.</p>
      </div>
    </section>

    <TablaCatalogo ruta="grupos-atributo" @cambio="cargar" />

    <Modal v-if="editando" lateral ancho="560px" :titulo="editando.id ? `Editar ${e.nombre || 'atributo'}` : 'Nuevo atributo'"
           descripcion="Defina el atributo una vez; después asígnelo a los tipos de producto." @cerrar="editando = null">
      <form id="form-atributo" class="pila" @submit.prevent="guardar">
        <div class="rejilla-2">
          <Campo etiqueta="Nombre" id="a-nombre" :error="errores.nombre" obligatorio>
            <input id="a-nombre" v-model="e.nombre" class="control" required maxlength="100" @input="codigoDesdeNombre" />
          </Campo>
          <Campo etiqueta="Código" id="a-codigo" :error="errores.codigo" ayuda="Minúsculas, números y _" obligatorio>
            <input id="a-codigo" v-model="e.codigo" class="control mono" required pattern="[a-z][a-z0-9_]*" maxlength="40"
                   @input="editando.codigoTocado = true" />
          </Campo>
        </div>
        <Campo etiqueta="Descripción" id="a-desc" ayuda="Se muestra como ayuda al capturar el valor.">
          <input id="a-desc" v-model="e.descripcion" class="control" maxlength="500" />
        </Campo>

        <fieldset class="tipos">
          <legend class="etiqueta">Tipo de dato</legend>
          <label v-for="(n, k) in TIPOS_DATO" :key="k" class="tipo" :class="{ elegido: e.tipo_dato === k }">
            <input v-model="e.tipo_dato" type="radio" name="tipo_dato" :value="k" />
            <strong>{{ n }}</strong><span>{{ AYUDA_TIPO[k] }}</span>
          </label>
        </fieldset>
        <p v-if="errores.tipo_dato" class="error-campo">{{ errores.tipo_dato }}</p>

        <div v-if="esNumero" class="rejilla-2">
          <Campo etiqueta="Magnitud" id="a-mag" ayuda="Opcional: para capturar con unidad (kg, g, L…).">
            <select id="a-mag" v-model="e.magnitud_id" class="control" @change="e.unidad_defecto_id = null">
              <option :value="null">Sin unidad</option>
              <option v-for="m in magnitudes" :key="m.id" :value="m.id">{{ m.nombre }}</option>
            </select>
          </Campo>
          <Campo v-if="e.magnitud_id" etiqueta="Unidad por defecto" id="a-unidad">
            <select id="a-unidad" v-model="e.unidad_defecto_id" class="control">
              <option :value="null">Ninguna</option>
              <option v-for="u in unidadesMagnitud" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
            </select>
          </Campo>
        </div>

        <Campo v-if="e.tipo_dato === 'referencia'" etiqueta="Apunta a" id="a-ent" obligatorio>
          <select id="a-ent" v-model="e.entidad_referencia" class="control" required>
            <option :value="null" disabled>Elegir…</option>
            <option v-for="x in entidades" :key="x" :value="x">{{ x }}</option>
          </select>
        </Campo>

        <div v-if="REGLAS[e.tipo_dato]" class="bloque">
          <h3>Reglas de validación</h3>
          <div class="rejilla-3">
            <Campo v-for="r in REGLAS[e.tipo_dato]" :key="r.k" :etiqueta="r.n" :id="`a-r-${r.k}`">
              <input :id="`a-r-${r.k}`" v-model="e.reglas[r.k]" class="control" :class="{ mono: r.texto }"
                     :type="r.texto ? 'text' : r.fecha ? 'date' : 'number'" step="any" />
            </Campo>
          </div>
          <p v-if="errores.reglas" class="error-campo">{{ errores.reglas }}</p>
        </div>

        <div v-if="conOpciones" class="bloque">
          <div class="fila entre">
            <h3>Opciones</h3>
            <button class="btn chico" type="button" @click="agregarOpcion"><Icono nombre="mas" :tam="14" />Agregar opción</button>
          </div>
          <div v-if="e.opciones.length" class="opciones">
            <div class="opcion-fila encabezado"><span>Nombre</span><span>Código</span><span>Activa</span><span /></div>
            <div v-for="(o, i) in e.opciones" :key="o.id || `n${i}`" class="opcion-fila">
              <input v-model="o.nombre" class="control" :aria-label="`Nombre de la opción ${i + 1}`" placeholder="Negro" @input="codigoOpcion(o)" />
              <input v-model="o.codigo" class="control mono" :aria-label="`Código de la opción ${i + 1}`" placeholder="NEGRO" @input="o.codigoTocado = true" />
              <label class="interruptor"><input v-model="o.activa" type="checkbox" :aria-label="`Opción ${i + 1} activa`" /></label>
              <button class="btn fantasma icono chico peligro" type="button" :aria-label="`Quitar opción ${o.nombre || i + 1}`" @click="e.opciones.splice(i, 1)"><Icono nombre="cerrar" :tam="14" /></button>
            </div>
          </div>
          <p v-else class="tenue chico">Agregue las opciones que se podrán elegir.</p>
        </div>

        <div class="rejilla-2">
          <Campo etiqueta="Grupo" id="a-grupo" ayuda="Sección de la ficha donde aparece.">
            <select id="a-grupo" v-model="e.grupo_id" class="control">
              <option :value="null">Sin grupo</option>
              <option v-for="g in grupos" :key="g.id" :value="g.id">{{ g.nombre }}</option>
            </select>
          </Campo>
          <Campo etiqueta="Orden" id="a-orden"><input id="a-orden" v-model="e.orden" class="control" type="number" /></Campo>
        </div>
        <label class="interruptor"><input v-model="e.activo" type="checkbox" />Activo</label>
      </form>
      <template #pie>
        <button class="btn" type="button" @click="editando = null">Cancelar</button>
        <button class="btn primario" type="submit" form="form-atributo" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar atributo</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.filtros { display: flex; gap: var(--e-3); padding: var(--e-4); border-bottom: 1px solid var(--linea); flex-wrap: wrap; }
.busqueda { position: relative; min-width: 220px; }
.busqueda svg { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--tinta-3); pointer-events: none; }
.busqueda .control { padding-left: 32px; }
.tipo-filtro { width: 220px; }
.nombre { font-weight: 550; }
.sin-resultados { padding: var(--e-5); text-align: center; }
.tipos { border: 0; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--e-2); }
.tipos legend { margin-bottom: var(--e-2); }
.tipo { display: flex; flex-direction: column; gap: 2px; padding: var(--e-3); border: 1px solid var(--borde-control); border-radius: var(--radio); cursor: pointer; transition: border-color 0.15s, background-color 0.15s; position: relative; }
.tipo input { position: absolute; opacity: 0; }
.tipo strong { font-size: 13.5px; font-weight: 600; }
.tipo span { font-size: 12px; color: var(--tinta-3); }
.tipo:hover { border-color: var(--acento); }
.tipo.elegido { border-color: var(--acento); background: var(--acento-claro); box-shadow: 0 0 0 1px var(--acento); }
.tipo:has(input:focus-visible) { outline: 2px solid var(--acento); outline-offset: 2px; }
.bloque { display: flex; flex-direction: column; gap: var(--e-3); padding: var(--e-4); border-radius: var(--radio); background: var(--superficie-2); border: 1px solid var(--linea); }
.rejilla-3 { display: grid; gap: var(--e-3); grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
.opciones { display: flex; flex-direction: column; gap: 6px; }
.opcion-fila { display: grid; grid-template-columns: 1.4fr 1fr 52px 30px; gap: var(--e-2); align-items: center; }
.opcion-fila.encabezado { font-size: 12px; color: var(--tinta-3); font-weight: 600; }
</style>
