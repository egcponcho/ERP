<script setup>
// Características (atributos): el editor completo a la izquierda y la tabla común
// a la derecha. Elegir una fila la carga en el editor; las opciones se editan
// como líneas del mismo formulario.
import { computed, onMounted, reactive, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import { TIPOS_DATO } from '@/nucleo/formato.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const filas = ref([])
const cargando = ref(true)
const listas = reactive({ magnitudes: [], unidades: [], grupos: [], entidades: [] })
const form = ref(null)
const errores = ref({})
const ocupado = ref(false)

const AYUDA = {
  texto: 'Nombre, número CAS, temporada…', entero: 'Vida útil en días, garantía…', decimal: 'Pureza, peso, voltaje…', booleano: 'Peligroso, vegano…',
  fecha: 'Vencimiento, lanzamiento…', opcion: 'Una de una lista: color, talla', opciones: 'Varias de una lista: alérgenos', referencia: 'Otro registro: producto base',
}
const REGLAS = {
  texto: [['longitud_min', 'Largo mínimo'], ['longitud_max', 'Largo máximo'], ['patron', 'Formato (expresión regular)', 'texto']],
  entero: [['minimo', 'Mínimo'], ['maximo', 'Máximo']],
  decimal: [['minimo', 'Mínimo'], ['maximo', 'Máximo'], ['decimales', 'Decimales']],
  fecha: [['minimo', 'Desde', 'fecha'], ['maximo', 'Hasta', 'fecha']],
  opciones: [['minimo', 'Elegir al menos'], ['maximo', 'Elegir como máximo']],
}
const COLUMNAS = [
  { clave: 'nombre', texto: 'Característica', fija: true },
  { clave: 'tipo_dato', texto: 'Tipo de dato', valor: (f) => TIPOS_DATO[f.tipo_dato] },
  { clave: 'detalle', texto: 'Detalle', filtro: false, ordenable: false },
  { clave: 'grupo', texto: 'Sección', valor: (f) => listas.grupos.find((g) => g.id === f.grupo_id)?.nombre },
  { clave: 'activo', texto: 'Activa', valor: (f) => f.activo, textoValor: (v) => (v ? 'Sí' : 'No') },
]

async function cargar() {
  cargando.value = true
  try {
    const [a, m, u, g, e] = await Promise.all([catalogo('atributos', { recargar: true }), catalogo('magnitudes'), catalogo('unidades'),
      catalogo('grupos-atributo', { recargar: true }), api.get(`${CONFIG}/entidades-referenciables`)])
    filas.value = a
    Object.assign(listas, { magnitudes: m, unidades: u, grupos: g, entidades: e })
  } catch (e) { avisarError(e) } finally { cargando.value = false }
}
onMounted(async () => { await cargar(); nuevo() })

function nuevo() {
  errores.value = {}
  form.value = { id: null, codigoTocado: false, d: { codigo: '', nombre: '', descripcion: '', tipo_dato: 'opcion', magnitud_id: null, unidad_defecto_id: null,
    entidad_referencia: null, reglas: {}, grupo_id: null, orden: 0, activo: true, opciones: [] }, originales: [] }
}
function elegir(a) {
  errores.value = {}
  form.value = { id: a.id, codigoTocado: true, d: { ...a, descripcion: a.descripcion || '', reglas: { ...a.reglas }, opciones: a.opciones.map((o) => ({ ...o })) },
    originales: a.opciones.map((o) => ({ ...o })) }
}
const d = computed(() => form.value?.d)
const esNumero = computed(() => ['entero', 'decimal'].includes(d.value?.tipo_dato))
const conOpciones = computed(() => ['opcion', 'opciones'].includes(d.value?.tipo_dato))
const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '')
function alNombre() {
  if (!form.value.codigoTocado) d.value.codigo = norm(d.value.nombre).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').replace(/^(\d)/, 'a_$1').slice(0, 40)
}
function agregarOpcion() {
  d.value.opciones.push({ codigo: '', nombre: '', orden: d.value.opciones.length + 1, activa: true, nueva: true })
}
function codigoOpcion(o) {
  if (o.nueva && !o.tocado) o.codigo = norm(o.nombre).toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 40)
}
function reglas() {
  const res = {}
  for (const [k, , tipo] of REGLAS[d.value.tipo_dato] || []) {
    const v = d.value.reglas[k]
    if (v !== '' && v !== null && v !== undefined) res[k] = tipo ? v : Number(v)
  }
  return res
}

async function guardar() {
  ocupado.value = true
  errores.value = {}
  const x = d.value
  const cuerpo = { codigo: x.codigo, nombre: x.nombre, descripcion: x.descripcion || null, tipo_dato: x.tipo_dato,
    magnitud_id: esNumero.value ? x.magnitud_id : null, unidad_defecto_id: esNumero.value && x.magnitud_id ? x.unidad_defecto_id : null,
    entidad_referencia: x.tipo_dato === 'referencia' ? x.entidad_referencia : null, reglas: reglas(), grupo_id: x.grupo_id, orden: Number(x.orden) || 0, activo: x.activo }
  const opciones = conOpciones.value ? x.opciones.filter((o) => o.nombre.trim()) : []
  try {
    let id = form.value.id
    if (!id) {
      id = (await api.post(`${CONFIG}/atributos`, { ...cuerpo, opciones: opciones.map((o, i) => ({ codigo: o.codigo, nombre: o.nombre, orden: i + 1, activa: o.activa })) })).id
    } else {
      await api.patch(`${CONFIG}/atributos/${id}`, cuerpo)
      for (const [i, o] of opciones.entries()) {
        const datos = { codigo: o.codigo, nombre: o.nombre, orden: i + 1, activa: o.activa }
        if (o.nueva) await api.post(`${CONFIG}/atributos/${id}/opciones`, datos)
        else {
          const antes = form.value.originales.find((y) => y.id === o.id)
          if (['codigo', 'nombre', 'orden', 'activa'].some((k) => antes[k] !== datos[k])) await api.patch(`${CONFIG}/atributos/${id}/opciones/${o.id}`, datos)
        }
      }
      for (const o of form.value.originales) if (!opciones.some((y) => y.id === o.id)) await api.del(`${CONFIG}/atributos/${id}/opciones/${o.id}`)
    }
    avisar(form.value.id ? `${x.nombre}: guardada.` : `Se creó la característica ${x.nombre}.`)
    invalidarCatalogo('atributos')
    await cargar()
    elegir(filas.value.find((a) => a.id === id))
  } catch (e) { errores.value = { ...e.porCampo, _general: e.message } } finally { ocupado.value = false }
}
async function borrar() {
  try {
    await api.del(`${CONFIG}/atributos/${form.value.id}`)
    avisar('Característica borrada.')
    invalidarCatalogo('atributos')
    await cargar()
    nuevo()
  } catch (e) { avisarError(e) }
}
function detalle(a) {
  if (a.opciones.length) return a.opciones.slice(0, 4).map((o) => o.nombre).join(', ') + (a.opciones.length > 4 ? ` y ${a.opciones.length - 4} más` : '')
  if (a.magnitud_id) return `${listas.magnitudes.find((m) => m.id === a.magnitud_id)?.nombre || ''}${a.unidad_defecto ? ` · ${a.unidad_defecto}` : ''}`
  if (a.entidad_referencia) return `→ ${a.entidad_referencia}`
  return ''
}
</script>

<template>
  <div>
    <div class="seccion-cabeza"><h2>Características</h2>
      <p class="ayuda">Lo que puede describir a un producto: color, talla, peso, pureza, vida útil… Se definen una vez y se usan en los tipos de producto.</p></div>
    <div class="mantenimiento ancho">
      <form v-if="form" class="panel form-catalogo" @submit.prevent="guardar">
        <div class="fila-flex entre">
          <h3>{{ form.id ? `Editar ${d.nombre || 'característica'}` : 'Nueva característica' }}</h3>
          <button v-if="form.id" type="button" class="btn btn-chico btn-fantasma" @click="nuevo"><Icono nombre="mas" :tam="14" />Nueva</button>
        </div>
        <p v-if="errores._general" class="nota error">{{ errores._general }}</p>
        <label class="campo" :class="{ 'con-error': errores.nombre }"><span class="req">Nombre</span><input v-model="d.nombre" class="entrada" maxlength="100" @input="alNombre" /></label>
        <label class="campo" :class="{ 'con-error': errores.codigo }"><span class="req">Código</span>
          <input v-model="d.codigo" class="entrada mono" maxlength="40" @input="form.codigoTocado = true" />
          <small class="ayuda">Minúsculas, números y _. Se usa en filtros y plantillas de SKU.</small></label>
        <div class="campo"><span class="req">Cómo se captura</span>
          <div class="tipos-dato" role="radiogroup" aria-label="Tipo de dato">
            <button v-for="(n, k) in TIPOS_DATO" :key="k" type="button" role="radio" class="tarjeta-eleccion tipo-dato" :aria-checked="d.tipo_dato === k" @click="d.tipo_dato = k">
              <b>{{ n }}</b><small>{{ AYUDA[k] }}</small></button>
          </div>
          <small v-if="errores.tipo_dato" class="campo-error">{{ errores.tipo_dato }}</small></div>
        <template v-if="esNumero">
          <label class="campo"><span>Se mide en</span>
            <select v-model="d.magnitud_id" class="entrada" @change="d.unidad_defecto_id = null"><option :value="null">Sin unidad</option>
              <option v-for="m in listas.magnitudes" :key="m.id" :value="m.id">{{ m.nombre }}</option></select></label>
          <label v-if="d.magnitud_id" class="campo"><span>Unidad habitual</span>
            <select v-model="d.unidad_defecto_id" class="entrada"><option :value="null">Ninguna</option>
              <option v-for="u in listas.unidades.filter((x) => x.magnitud_id === d.magnitud_id)" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option></select></label>
        </template>
        <label v-if="d.tipo_dato === 'referencia'" class="campo"><span class="req">Apunta a</span>
          <select v-model="d.entidad_referencia" class="entrada"><option :value="null" disabled>Elegir…</option><option v-for="x in listas.entidades" :key="x" :value="x">{{ x }}</option></select></label>
        <div v-if="REGLAS[d.tipo_dato]" class="bloque">
          <p class="resumen-titulo">Reglas de validación</p>
          <div class="rejilla-reglas">
            <label v-for="[k, n, tipo] in REGLAS[d.tipo_dato]" :key="k" class="campo"><span>{{ n }}</span>
              <input v-model="d.reglas[k]" class="entrada" :class="{ mono: tipo === 'texto' }" :type="tipo === 'texto' ? 'text' : tipo === 'fecha' ? 'date' : 'number'" step="any" /></label>
          </div>
          <small v-if="errores.reglas" class="campo-error">{{ errores.reglas }}</small>
        </div>
        <div v-if="conOpciones" class="bloque">
          <div class="fila-flex entre"><p class="resumen-titulo mb-0">Opciones</p>
            <button type="button" class="btn btn-chico" @click="agregarOpcion"><Icono nombre="mas" :tam="13" />Agregar</button></div>
          <div v-for="(o, i) in d.opciones" :key="o.id || `n${i}`" class="opcion-fila">
            <input v-model="o.nombre" class="entrada entrada-chica" placeholder="Nombre" :aria-label="`Nombre de la opción ${i + 1}`" @input="codigoOpcion(o)" />
            <input v-model="o.codigo" class="entrada entrada-chica mono" placeholder="CÓDIGO" :aria-label="`Código de la opción ${i + 1}`" @input="o.tocado = true" />
            <label class="check" :title="o.activa ? 'Activa' : 'Inactiva'"><input v-model="o.activa" type="checkbox" :aria-label="`Opción ${i + 1} activa`" /></label>
            <button type="button" class="btn-icono" :aria-label="`Quitar la opción ${o.nombre || i + 1}`" @click="d.opciones.splice(i, 1)"><Icono nombre="cerrar" :tam="14" /></button>
          </div>
          <p v-if="!d.opciones.length" class="ayuda">Agregue las opciones que se podrán elegir.</p>
        </div>
        <label class="campo"><span>Sección de la ficha</span>
          <select v-model="d.grupo_id" class="entrada"><option :value="null">Sin sección</option><option v-for="g in listas.grupos" :key="g.id" :value="g.id">{{ g.nombre }}</option></select></label>
        <label class="campo"><span>Descripción (ayuda al capturar)</span><input v-model="d.descripcion" class="entrada" maxlength="500" /></label>
        <label class="check"><input v-model="d.activo" type="checkbox" />Activa</label>
        <div class="fila-flex">
          <BotonConfirmar v-if="form.id" :etiqueta="`Borrar ${d.nombre}`" texto="Borrar" pregunta="¿Borrar? Si está en uso, desactívela." @confirmar="borrar" />
          <button type="submit" class="btn btn-primario separar" :disabled="ocupado"><Icono nombre="check" :tam="16" />{{ form.id ? 'Guardar' : 'Crear' }}</button>
        </div>
      </form>
      <TablaDatos tabla="config-atributos" :columnas="COLUMNAS" :filas="filas" :cargando="cargando" fila-clicable :fila-activa="form?.id" orden-inicial="nombre:asc"
                  etiqueta="Características" @fila="elegir">
        <template #celda-nombre="{ fila }"><b>{{ fila.nombre }}</b><span class="sub mono">{{ fila.codigo }}</span></template>
        <template #celda-tipo_dato="{ fila }"><span class="etiqueta info ms-0">{{ TIPOS_DATO[fila.tipo_dato] }}</span></template>
        <template #celda-detalle="{ fila }"><span class="apagado envolver">{{ detalle(fila) || '—' }}</span></template>
        <template #celda-grupo="{ fila }">{{ listas.grupos.find((g) => g.id === fila.grupo_id)?.nombre || '—' }}</template>
        <template #celda-activo="{ fila }"><span class="estado" :class="fila.activo ? 'estado-ok' : 'estado-neutro'"><span class="estado-marca" />{{ fila.activo ? 'Activa' : 'Inactiva' }}</span></template>
        <template #vacio>Todavía no hay características. Cree la primera con el formulario de la izquierda.</template>
      </TablaDatos>
    </div>
  </div>
</template>

<style scoped>
.seccion-cabeza { margin-bottom: 14px; }
.mantenimiento.ancho { grid-template-columns: minmax(320px, 400px) minmax(0, 1fr); }
@media (max-width: 1100px) { .mantenimiento.ancho { grid-template-columns: minmax(0, 1fr); } }
.form-catalogo { max-height: none; }
.tipos-dato { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.tipo-dato { padding: 8px 10px; box-shadow: none; }
.tipo-dato b { font-size: 0.86rem; }
.tipo-dato small { font-size: 0.74rem; }
.bloque { display: flex; flex-direction: column; gap: 8px; padding: 12px; border: 1px solid var(--linea); border-radius: var(--radio); background: var(--superficie-2); }
.rejilla-reglas { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; }
.opcion-fila { display: grid; grid-template-columns: 1.3fr 1fr 24px 28px; gap: 6px; align-items: center; }
</style>
