<script setup>
// Un tipo de producto: sus datos, las características que pide (propias y
// heredadas, en la tabla común; cada fila se edita al abrirla) y una vista
// previa de la ficha que resulta.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import { TIPOS_DATO, valorTexto } from '@/nucleo/formato.js'
import BotonConfirmar from '@/componentes/BotonConfirmar.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import { fijarTitulo } from '@/nucleo/migas.js'
import PanelEnLinea from '@/componentes/PanelEnLinea.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'
import NuevaCaracteristica from '../asistente/NuevaCaracteristica.vue'

const props = defineProps({ id: { type: Number, required: true } })
const router = useRouter()
const tipo = ref(null)
const esquema = ref(null)
const datos = reactive({ tipos: [], atributos: [], unidades: [], magnitudes: [] })
const editando = ref(null) // datos generales
const erroresTipo = ref({})
const asignando = ref(null)
const creandoCaracteristica = ref(false)
const edicion = reactive({}) // atributo_id → { uso, obligatorio, valor_defecto, orden, error }
const previa = ref({})

async function cargar() {
  try {
    const [t, e, tipos, atributos, unidades, magnitudes] = await Promise.all([api.get(`${CONFIG}/tipos-producto/${props.id}`),
      api.get(`${CONFIG}/tipos-producto/${props.id}/esquema`), catalogo('tipos-producto', { recargar: true }), catalogo('atributos', { recargar: true }),
      catalogo('unidades'), catalogo('magnitudes')])
    tipo.value = t
    fijarTitulo(t.nombre)
    esquema.value = e
    Object.assign(datos, { tipos, atributos: [...atributos], unidades, magnitudes })
    for (const k of Object.keys(edicion)) delete edicion[k]
  } catch (e) {
    avisarError(e)
    if (e.status === 404) router.push('/productos/configuracion/tipos')
  }
}
onMounted(cargar)
watch(() => props.id, cargar)

const propias = computed(() => new Map((tipo.value?.asignaciones || []).map((a) => [a.atributo_id, a])))
const ocultos = computed(() => (tipo.value?.asignaciones || []).filter((a) => a.oculto).map((a) => ({ ...a, atributo: datos.atributos.find((x) => x.id === a.atributo_id) })))
const ruta = computed(() => (esquema.value?.ruta || []).map((c) => datos.tipos.find((t) => t.codigo === c)).filter(Boolean))
const disponibles = computed(() => {
  const usados = new Set([...(esquema.value?.campos || []).map((c) => c.atributo.id), ...(tipo.value?.asignaciones || []).map((a) => a.atributo_id)])
  return datos.atributos.filter((a) => a.activo && !usados.has(a.id))
})
const unidad = computed(() => datos.unidades.find((u) => u.id === esquema.value?.unidad_defecto_id))
const ejes = computed(() => (esquema.value?.campos || []).filter((c) => c.es_eje))
const usoDe = (c) => (c.es_eje ? 'eje' : c.nivel)
const USOS = { producto: 'Dato del producto', eje: 'Distingue variantes', variante: 'Dato de cada variante' }

const filas = computed(() => (esquema.value?.campos || []).map((c) => ({ ...c, id: c.atributo.id })))
const COLUMNAS = [
  { clave: 'nombre', texto: 'Característica', fija: true, valor: (f) => f.atributo.nombre },
  { clave: 'tipo_dato', texto: 'Tipo de dato', valor: (f) => TIPOS_DATO[f.atributo.tipo_dato] },
  { clave: 'uso', texto: 'Uso', valor: (f) => USOS[usoDe(f)] },
  { clave: 'obligatorio', texto: 'Obligatorio', valor: (f) => f.obligatorio || f.es_eje, textoValor: (v) => (v ? 'Sí' : 'No') },
  { clave: 'defecto', texto: 'Por defecto', filtro: false, valor: (f) => valorTexto(f.valor_defecto, f.atributo) },
  { clave: 'origen', texto: 'Origen', valor: (f) => (f.heredado_de ? `Heredado de ${f.heredado_de}` : 'Propio') },
]

// ---- Datos generales ----------------------------------------------------------------------
function editarTipo() {
  erroresTipo.value = {}
  const t = tipo.value
  editando.value = { nombre: t.nombre, codigo: t.codigo, descripcion: t.descripcion || '', padre_id: t.padre_id, unidad_defecto_id: t.unidad_defecto_id,
    plantilla_codigo: t.plantilla_codigo || '', siguiente_numero: t.siguiente_numero, plantilla_sku: t.plantilla_sku || '', activo: t.activo }
}
async function guardarTipo() {
  erroresTipo.value = {}
  const d = { ...editando.value }
  for (const k of ['descripcion', 'plantilla_codigo', 'plantilla_sku']) d[k] = d[k] || null
  d.siguiente_numero = Number(d.siguiente_numero) || 1
  try {
    await api.patch(`${CONFIG}/tipos-producto/${props.id}`, d)
    invalidarCatalogo('tipos-producto')
    avisar('Tipo guardado.')
    editando.value = null
    await cargar()
  } catch (e) { erroresTipo.value = { ...e.porCampo, _general: e.message } }
}
const padres = computed(() => {
  const excluir = new Set([props.id])
  let cambio = true
  while (cambio) {
    cambio = false
    for (const t of datos.tipos) if (t.padre_id && excluir.has(t.padre_id) && !excluir.has(t.id)) { excluir.add(t.id); cambio = true }
  }
  return datos.tipos.filter((t) => !excluir.has(t.id))
})
const ejemplo = computed(() => {
  const m = /\{seq(?::0?(\d+)d?)?\}/.exec(editando.value?.plantilla_codigo || '')
  return m ? editando.value.plantilla_codigo.replace(m[0], String(editando.value.siguiente_numero || 1).padStart(Number(m[1] || 0), '0')) : ''
})

// ---- Características: editar en la fila ------------------------------------------------------
function abrir(f) {
  edicion[f.id] = { uso: usoDe(f), obligatorio: f.obligatorio, valor_defecto: f.valor_defecto, orden: f.orden, error: '' }
}
function cuerpo(e) {
  return { nivel: e.uso === 'producto' ? 'producto' : 'variante', es_eje: e.uso === 'eje', obligatorio: e.uso !== 'eje' && e.obligatorio,
    valor_defecto: e.uso === 'eje' ? null : e.valor_defecto ?? null, orden: Number(e.orden) || 0 }
}
async function guardarFila(f) {
  const e = edicion[f.id]
  e.error = ''
  try {
    if (propias.value.has(f.id)) await api.patch(`${CONFIG}/tipos-producto/${props.id}/atributos/${f.id}`, cuerpo(e))
    else await api.post(`${CONFIG}/tipos-producto/${props.id}/atributos`, { atributo_id: f.id, ...cuerpo(e) })
    avisar(`${f.atributo.nombre}: guardado.`)
    await cargar()
  } catch (err) { e.error = err.message }
}
async function quitar(f) {
  try {
    if (f.heredado_de) {
      if (propias.value.has(f.id)) await api.patch(`${CONFIG}/tipos-producto/${props.id}/atributos/${f.id}`, { oculto: true })
      else await api.post(`${CONFIG}/tipos-producto/${props.id}/atributos`, { atributo_id: f.id, nivel: f.nivel, es_eje: f.es_eje, oculto: true })
      avisar(`${f.atributo.nombre} queda oculto en este tipo.`)
    } else {
      await api.del(`${CONFIG}/tipos-producto/${props.id}/atributos/${f.id}`)
      avisar(`${f.atributo.nombre} ya no es parte del tipo.`)
    }
    await cargar()
  } catch (e) { avisarError(e) }
}
async function restablecer(atributoId, mensaje) {
  try {
    await api.del(`${CONFIG}/tipos-producto/${props.id}/atributos/${atributoId}`)
    avisar(mensaje)
    await cargar()
  } catch (e) { avisarError(e) }
}

// ---- Asignar una característica --------------------------------------------------------------
function abrirAsignar() {
  asignando.value = { atributo_id: disponibles.value[0]?.id ?? null, uso: 'producto', obligatorio: false, valor_defecto: null, orden: 0, error: '' }
}
const atributoAsignar = computed(() => datos.atributos.find((a) => a.id === asignando.value?.atributo_id))
async function asignar() {
  asignando.value.error = ''
  try {
    await api.post(`${CONFIG}/tipos-producto/${props.id}/atributos`, { atributo_id: asignando.value.atributo_id, ...cuerpo(asignando.value) })
    avisar(`${atributoAsignar.value.nombre} se agregó al tipo.`)
    asignando.value = null
    await cargar()
  } catch (e) { asignando.value.error = e.message }
}
function caracteristicaCreada(a) {
  datos.atributos.push(a)
  invalidarCatalogo('atributos')
  creandoCaracteristica.value = false
  if (!asignando.value) abrirAsignar()
  asignando.value.atributo_id = a.id
}
</script>

<template>
  <div v-if="tipo && esquema">
    <p v-if="ruta.length > 1" class="ayuda mb-2">Subtipo de
      <template v-for="(t, i) in ruta.slice(0, -1)" :key="t.id">{{ i ? ' › ' : '' }}<RouterLink :to="`/productos/configuracion/tipos/${t.id}`">{{ t.nombre }}</RouterLink></template>
    </p>
    <header class="doc-cabeza">
      <div class="doc-fila">
        <span class="doc-numero">{{ tipo.nombre }}</span><code class="apagado">{{ tipo.codigo }}</code>
        <span v-if="!tipo.activo" class="estado estado-neutro"><span class="estado-marca" />Inactivo</span>
        <div class="doc-acciones">
          <RouterLink class="btn" :to="`/productos/catalogo?tipo=${tipo.codigo}`">Ver productos</RouterLink>
          <button v-if="!editando" type="button" class="btn" @click="editarTipo"><Icono nombre="editar" :tam="16" />Editar datos</button>
        </div>
      </div>
      <div v-if="tipo.descripcion" class="doc-sub">{{ tipo.descripcion }}</div>
      <div class="doc-datos">
        <div class="dato">Unidad base<b>{{ unidad ? `${unidad.nombre} (${unidad.codigo})` : 'Se elige en cada producto' }}</b></div>
        <div class="dato">Numeración<b class="mono">{{ tipo.plantilla_codigo || (tipo.padre_id ? 'Heredada' : 'Manual') }}</b></div>
        <div class="dato">SKU de variantes<b class="mono">{{ esquema.plantilla_sku || 'Automático' }}</b></div>
        <div class="dato">Variantes por<b>{{ ejes.map((c) => c.atributo.nombre).join(' × ') || 'Sin variantes' }}</b></div>
      </div>
    </header>

    <PanelEnLinea v-if="editando" :titulo="`Editar ${tipo.nombre}`" @cerrar="editando = null">
      <p v-if="erroresTipo._general" class="nota error mb-3">{{ erroresTipo._general }}</p>
      <div class="rejilla-campos">
        <label class="campo" :class="{ 'con-error': erroresTipo.nombre }"><span class="req">Nombre</span><input v-model="editando.nombre" class="entrada" maxlength="100" /></label>
        <label class="campo" :class="{ 'con-error': erroresTipo.codigo }"><span class="req">Código</span><input v-model="editando.codigo" class="entrada mono" maxlength="30" /></label>
        <label class="campo" :class="{ 'con-error': erroresTipo.padre_id }"><span>Dentro de</span>
          <select v-model="editando.padre_id" class="entrada"><option :value="null">Ninguno</option><option v-for="t in padres" :key="t.id" :value="t.id">{{ t.nombre }}</option></select></label>
        <label class="campo"><span>Unidad base</span>
          <select v-model="editando.unidad_defecto_id" class="entrada"><option :value="null">{{ editando.padre_id ? 'La del tipo padre' : 'Se elige en cada producto' }}</option>
            <option v-for="u in datos.unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option></select></label>
        <label class="campo" :class="{ 'con-error': erroresTipo.plantilla_codigo }"><span>Numeración</span>
          <input v-model="editando.plantilla_codigo" class="entrada mono" placeholder="CAL-{seq:05}" />
          <small class="ayuda">{{ ejemplo ? `El próximo será ${ejemplo}` : 'Vacío: el código se escribe a mano.' }}</small></label>
        <label class="campo"><span>Siguiente número</span><input v-model="editando.siguiente_numero" class="entrada num" type="number" min="1" /></label>
        <label class="campo col-2" :class="{ 'con-error': erroresTipo.plantilla_sku }"><span>SKU de las variantes</span>
          <input v-model="editando.plantilla_sku" class="entrada mono" placeholder="{producto}-{color}-{talla}" />
          <small class="ayuda">Use {producto} y los códigos de las características que distinguen variantes.</small></label>
        <label class="campo col-completa"><span>Descripción</span><input v-model="editando.descripcion" class="entrada" maxlength="500" /></label>
        <label class="check"><input v-model="editando.activo" type="checkbox" />Activo</label>
      </div>
      <template #pie>
        <button type="button" class="btn" @click="editando = null">Cancelar</button>
        <button type="button" class="btn btn-primario" @click="guardarTipo"><Icono nombre="check" :tam="16" />Guardar</button>
      </template>
    </PanelEnLinea>

    <div class="con-resumen">
      <div>
        <div class="fila-flex entre mb-3">
          <div><h2>Características</h2><p class="ayuda">Abra una fila para cambiarla. Las heredadas se pueden ajustar u ocultar solo en este tipo.</p></div>
          <div class="fila-flex">
            <button v-if="!creandoCaracteristica" type="button" class="btn" @click="creandoCaracteristica = true"><Icono nombre="mas" :tam="15" />Nueva característica</button>
            <button v-if="!asignando" type="button" class="btn btn-primario" :disabled="!disponibles.length" @click="abrirAsignar"><Icono nombre="mas" :tam="15" />Asignar existente</button>
          </div>
        </div>
        <NuevaCaracteristica v-if="creandoCaracteristica" :datos="datos" class="mb-3" @cerrar="creandoCaracteristica = false" @creada="caracteristicaCreada" />
        <PanelEnLinea v-if="asignando" titulo="Asignar característica" @cerrar="asignando = null">
          <p v-if="asignando.error" class="nota error mb-3">{{ asignando.error }}</p>
          <div class="rejilla-campos">
            <label class="campo"><span class="req">Característica</span>
              <select v-model="asignando.atributo_id" class="entrada"><option v-for="a in disponibles" :key="a.id" :value="a.id">{{ a.nombre }} · {{ TIPOS_DATO[a.tipo_dato] }}</option></select></label>
            <label class="campo"><span class="req">Uso</span>
              <select v-model="asignando.uso" class="entrada"><option v-for="(n, k) in USOS" :key="k" :value="k" :disabled="k === 'eje' && atributoAsignar?.tipo_dato === 'opciones'">{{ n }}</option></select></label>
            <label v-if="asignando.uso !== 'eje'" class="check"><input v-model="asignando.obligatorio" type="checkbox" />Obligatorio</label>
            <CampoAtributo v-if="atributoAsignar && asignando.uso !== 'eje'" v-model="asignando.valor_defecto" :campo="{ atributo: atributoAsignar }"
                           :unidades="datos.unidades" etiqueta="Valor por defecto (opcional)" id-base="asignar" />
          </div>
          <template #pie>
            <button type="button" class="btn" @click="asignando = null">Cancelar</button>
            <button type="button" class="btn btn-primario" :disabled="!asignando.atributo_id" @click="asignar"><Icono nombre="check" :tam="16" />Asignar</button>
          </template>
        </PanelEnLinea>

        <TablaDatos tabla="config-tipo-caracteristicas" :columnas="COLUMNAS" :filas="filas" expandible etiqueta="Características del tipo" @expandir="abrir">
          <template #celda-nombre="{ fila }"><b>{{ fila.atributo.nombre }}</b><code class="apagado ms-1">{{ fila.atributo.codigo }}</code></template>
          <template #celda-tipo_dato="{ fila }">{{ TIPOS_DATO[fila.atributo.tipo_dato] }}</template>
          <template #celda-uso="{ fila }"><span class="etiqueta ms-0" :class="{ acento: fila.es_eje }">{{ USOS[usoDe(fila)] }}</span></template>
          <template #celda-obligatorio="{ fila }"><span :class="{ apagado: !(fila.obligatorio || fila.es_eje) }">{{ fila.es_eje ? 'Siempre' : fila.obligatorio ? 'Sí' : 'No' }}</span></template>
          <template #celda-defecto="{ fila }">{{ valorTexto(fila.valor_defecto, fila.atributo) }}</template>
          <template #celda-origen="{ fila }"><span v-if="fila.heredado_de" class="apagado"><Icono nombre="heredado" :tam="13" /> {{ fila.heredado_de }}<template v-if="propias.has(fila.id)"> · ajustado aquí</template></span>
            <span v-else>Propio</span></template>
          <template #acciones="{ fila }">
            <BotonConfirmar :etiqueta="`${fila.heredado_de ? 'Ocultar' : 'Quitar'} ${fila.atributo.nombre}`" :icono="fila.heredado_de ? 'ojo-no' : 'basura'"
                            :pregunta="fila.heredado_de ? '¿Ocultar aquí?' : '¿Quitar del tipo?'" :confirmar="fila.heredado_de ? 'Sí, ocultar' : 'Sí, quitar'" @confirmar="quitar(fila)" />
          </template>
          <template #detalle="{ fila }">
            <form v-if="edicion[fila.id]" class="edicion" @submit.prevent="guardarFila(fila)">
              <p v-if="edicion[fila.id].error" class="nota error">{{ edicion[fila.id].error }}</p>
              <div class="rejilla-campos">
                <label class="campo"><span>Uso</span>
                  <select v-model="edicion[fila.id].uso" class="entrada"><option v-for="(n, k) in USOS" :key="k" :value="k" :disabled="k === 'eje' && fila.atributo.tipo_dato === 'opciones'">{{ n }}</option></select></label>
                <label v-if="edicion[fila.id].uso !== 'eje'" class="check"><input v-model="edicion[fila.id].obligatorio" type="checkbox" />Obligatorio</label>
                <CampoAtributo v-if="edicion[fila.id].uso !== 'eje'" v-model="edicion[fila.id].valor_defecto" :campo="{ atributo: fila.atributo }" :unidades="datos.unidades"
                               etiqueta="Valor por defecto" :id-base="`def${fila.id}`" />
                <label class="campo"><span>Orden</span><input v-model="edicion[fila.id].orden" class="entrada num ancho-s" type="number" /></label>
              </div>
              <div class="fila-flex">
                <button type="submit" class="btn btn-primario btn-chico"><Icono nombre="check" :tam="14" />{{ fila.heredado_de && !propias.has(fila.id) ? 'Ajustar solo en este tipo' : 'Guardar' }}</button>
                <button v-if="fila.heredado_de && propias.has(fila.id)" type="button" class="btn btn-chico btn-fantasma" @click="restablecer(fila.id, 'Se usa otra vez lo heredado.')">Volver a lo heredado</button>
              </div>
            </form>
          </template>
          <template #vacio>Este tipo aún no tiene características. Asigne una existente o cree una nueva.</template>
        </TablaDatos>
        <div v-if="ocultos.length" class="chips mt">
          <span class="ayuda">Ocultas en este tipo:</span>
          <span v-for="a in ocultos" :key="a.atributo_id" class="chip">{{ a.atributo?.nombre }}
            <button type="button" :aria-label="`Mostrar otra vez ${a.atributo?.nombre}`" title="Mostrar otra vez" @click="restablecer(a.atributo_id, 'La característica vuelve a mostrarse.')"><Icono nombre="ojo" :tam="13" /></button></span>
        </div>
      </div>

      <aside class="panel">
        <p class="resumen-titulo">Vista previa de la ficha</p>
        <div class="pila-previa">
          <CampoAtributo v-for="c in esquema.campos.filter((x) => x.nivel === 'producto')" :key="c.atributo.id" v-model="previa[c.atributo.codigo]" :campo="c" :unidades="datos.unidades" id-base="previa" />
          <p v-if="!esquema.campos.some((x) => x.nivel === 'producto')" class="ayuda">Sin características del producto.</p>
          <template v-if="esquema.campos.some((x) => x.nivel === 'variante')">
            <p class="resumen-titulo mt">Cada variante</p>
            <CampoAtributo v-for="c in esquema.campos.filter((x) => x.nivel === 'variante')" :key="c.atributo.id" v-model="previa[`v_${c.atributo.codigo}`]" :campo="c" :unidades="datos.unidades" id-base="previa-v" />
          </template>
        </div>
      </aside>
    </div>
  </div>
  <div v-else class="doc-cabeza" aria-busy="true"><span class="esqueleto" style="width: 240px; height: 26px" /></div>
</template>

<style scoped>
.edicion { display: flex; flex-direction: column; gap: 10px; }
.pila-previa { display: flex; flex-direction: column; gap: 12px; }
.ms-1 { margin-inline-start: 6px; }
</style>
