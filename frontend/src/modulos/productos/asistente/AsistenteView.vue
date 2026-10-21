<script setup>
// Asistente de alta de productos (el mismo patrón que el de órdenes de compra de
// facturacion): un paso a la vez, se puede volver a cualquiera sin perder lo
// escrito, el borrador se guarda solo y al final se revisa todo con los códigos
// reales antes de crear. El alta completa se guarda en una sola transacción.
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import Asistente from '@/componentes/Asistente.vue'
import Icono from '@/componentes/Icono.vue'
import { b, cargarBorrador, claveCombinacion, combinaciones, descartarBorrador, guardarBorrador, nuevoBorrador } from './borrador.js'
import PasoTipo from './PasoTipo.vue'
import PasoGeneral from './PasoGeneral.vue'
import PasoCaracteristicas from './PasoCaracteristicas.vue'
import PasoVariantes from './PasoVariantes.vue'
import PasoEmpaque from './PasoEmpaque.vue'
import PasoClasificacion from './PasoClasificacion.vue'
import PasoRevisar from './PasoRevisar.vue'
import ResumenAlta from './ResumenAlta.vue'

const router = useRouter()
const recuperado = ref(false)
const esquema = ref(null)
const datos = reactive({ tipos: [], atributos: [], unidades: [], magnitudes: [], estados: [], tiposIdentificador: [], listos: false })
const errores = ref([]) // [{campo, mensaje, faltantes?}] del servidor
const previa = ref(null) // resultado de la validación (sin guardar)
const ocupado = ref(false)

onMounted(async () => {
  const guardado = cargarBorrador()
  Object.assign(b, nuevoBorrador())
  if (guardado && (guardado.tipoId || guardado.producto.nombre)) {
    Object.assign(b, guardado)
    recuperado.value = true
  }
  await cargarDatos()
  if (b.tipoId) await cargarEsquema()
  // Si se retoma en el último paso, se revisa otra vez con los datos de ahora
  if (paso.value?.clave === 'revisar') validar()
})

async function cargarDatos() {
  try {
    const [tipos, atributos, unidades, magnitudes, estados, ti] = await Promise.all([catalogo('tipos-producto', { recargar: true }),
      catalogo('atributos', { recargar: true }), catalogo('unidades'), catalogo('magnitudes'), catalogo('estados', { recargar: true }),
      catalogo('tipos-identificador', { recargar: true })])
    Object.assign(datos, { tipos, atributos: [...atributos], unidades, magnitudes, estados, tiposIdentificador: ti.filter((x) => x.activo), listos: true })
  } catch (e) { avisarError(e) }
}

async function cargarEsquema() {
  try {
    esquema.value = await api.get(`${CONFIG}/tipos-producto/${b.tipoId}/esquema`)
  } catch (e) {
    avisarError(e)
    b.tipoId = null
    esquema.value = null
  }
}

// Guardado automático del borrador
let reloj = null
watch(b, () => { clearTimeout(reloj); reloj = setTimeout(() => guardarBorrador(b), 400) }, { deep: true })
const guardado = computed(() => (b.guardadoEn ? `Borrador guardado · ${new Date(b.guardadoEn).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' })}` : ''))

// ---- Elegir el tipo ---------------------------------------------------------------------
async function elegirTipo(tipo) {
  const cambia = b.tipoId !== tipo.id
  b.tipoId = tipo.id
  await cargarEsquema()
  if (cambia) {
    // Otro tipo: los datos propios del anterior ya no aplican; se ponen los valores por defecto del nuevo
    b.producto.atributos = {}
    for (const c of esquema.value.campos) if (c.nivel === 'producto' && c.valor_defecto !== null && c.valor_defecto !== undefined) b.producto.atributos[c.atributo.codigo] = c.valor_defecto
    b.ejes = {}
    b.comunes = {}
    b.excluidas = []
    b.producto.unidad_id = esquema.value.unidad_defecto_id
  }
  if (!b.producto.unidad_id) b.producto.unidad_id = esquema.value.unidad_defecto_id
  errores.value = []
  ir(1)
}
async function tipoCreado(tipo) {
  invalidarCatalogo('tipos-producto')
  invalidarCatalogo('atributos')
  await cargarDatos()
  await elegirTipo(tipo)
}

// ---- Pasos ------------------------------------------------------------------------------
const ejes = computed(() => (esquema.value?.campos || []).filter((c) => c.es_eje))
const camposProducto = computed(() => (esquema.value?.campos || []).filter((c) => c.nivel === 'producto'))
const combos = computed(() => combinaciones(ejes.value, b.ejes))
const incluidas = computed(() => combos.value.filter((c) => !b.excluidas.includes(claveCombinacion(c))))
const faltanObligatorios = computed(() => camposProducto.value.filter((c) => c.obligatorio && vacio(b.producto.atributos[c.atributo.codigo])))
const vacio = (v) => v === null || v === undefined || v === '' || (Array.isArray(v) && !v.length) || (typeof v === 'object' && !Array.isArray(v) && (v.valor === '' || v.valor === null))

// Paso de cada error del servidor según su camino
function pasoDe(campo) {
  if (campo.startsWith('producto.atributos')) return 'caracteristicas'
  if (campo.startsWith('producto.categorias')) return 'clasificacion'
  if (campo.startsWith('producto')) return 'general'
  if (campo.startsWith('variantes')) return 'variantes'
  if (campo.startsWith('presentaciones') || campo.startsWith('identificadores')) return 'empaque'
  return 'revisar'
}
const erroresDe = (clave) => errores.value.filter((e) => pasoDe(e.campo) === clave)

const pasos = computed(() => {
  const sinTipo = !b.tipoId || !esquema.value
  const lista = [
    { clave: 'tipo', titulo: 'Tipo de producto', completo: !!b.tipoId },
    { clave: 'general', titulo: 'Datos generales', completo: !!b.producto.nombre.trim() && !!b.producto.unidad_id, bloqueado: sinTipo },
    { clave: 'caracteristicas', titulo: 'Características', completo: !sinTipo && !faltanObligatorios.value.length, bloqueado: sinTipo },
  ]
  if (ejes.value.length) lista.push({ clave: 'variantes', titulo: 'Variantes', completo: incluidas.value.length > 0, bloqueado: sinTipo })
  lista.push(
    { clave: 'empaque', titulo: 'Empaque y códigos', completo: b.presentaciones.length > 0 || b.identificadores.length > 0, bloqueado: sinTipo },
    { clave: 'clasificacion', titulo: 'Categorías', completo: b.producto.categorias.length > 0, bloqueado: sinTipo },
    { clave: 'revisar', titulo: 'Revisar y crear', completo: false, bloqueado: sinTipo || !b.producto.nombre.trim() },
  )
  return lista.map((p) => ({ ...p, errores: erroresDe(p.clave).length }))
})
const actual = computed(() => Math.min(b.paso, pasos.value.length - 1))
const paso = computed(() => pasos.value[actual.value])

function ir(i) {
  b.paso = Math.max(0, Math.min(i, pasos.value.length - 1))
  window.scrollTo({ top: 0, behavior: 'smooth' })
  if (pasos.value[b.paso]?.clave === 'revisar') validar()
}
function siguiente() {
  if (paso.value.clave === 'tipo' && !b.tipoId) return avisar('Elija el tipo de producto o cree uno nuevo.', 'info')
  if (paso.value.clave === 'general' && !b.producto.nombre.trim()) return avisar('Escriba el nombre del producto.', 'info')
  ir(actual.value + 1)
}

// ---- Lo que se envía ---------------------------------------------------------------------
function cuerpo() {
  const limpio = (o) => Object.fromEntries(Object.entries(o).filter(([, v]) => !vacio(v)))
  return {
    producto: { tipo_id: b.tipoId, nombre: b.producto.nombre.trim(), codigo: b.producto.codigo.trim() || null,
      descripcion: b.producto.descripcion || null, unidad_id: b.producto.unidad_id, atributos: limpio(b.producto.atributos),
      categorias: b.producto.categorias },
    variantes: incluidas.value.map((c) => ({ atributos: { ...limpio(b.comunes), ...c } })),
    presentaciones: b.presentaciones.filter((x) => x.nombre || x.codigo)
      .map((x) => ({ codigo: x.codigo, nombre: x.nombre, unidad_id: x.unidad_id, cantidad: x.cantidad === '' ? null : Number(x.cantidad) })),
    identificadores: b.identificadores.filter((x) => x.valor).map((x) => ({ tipo_id: x.tipo_id, valor: x.valor, presentacion_codigo: x.presentacion_codigo || null })),
    estado_id: b.estadoId,
  }
}

function leerErrores(e) {
  if (Array.isArray(e.detalle)) errores.value = e.detalle.map((d) => ({ campo: d.campo || 'revisar', mensaje: d.mensaje, faltantes: d.faltantes }))
  else errores.value = [{ campo: 'revisar', mensaje: e.message }]
}

async function validar() {
  ocupado.value = true
  previa.value = null
  try {
    previa.value = await api.post('/productos/asistente?validar=true', cuerpo())
    errores.value = []
  } catch (e) {
    if (e.status === 422 || e.status === 409 || e.status === 404) leerErrores(e)
    else avisarError(e)
  } finally { ocupado.value = false }
}

async function crear() {
  ocupado.value = true
  try {
    const p = await api.post('/productos/asistente', cuerpo())
    descartarBorrador()
    clearTimeout(reloj)
    avisar(`Se creó ${p.codigo} · ${p.nombre}${p.variantes.length ? ` con ${p.variantes.length} variantes` : ''}.`)
    router.push(`/productos/${p.id}`)
  } catch (e) {
    if (e.detalle) {
      leerErrores(e)
      avisar('Hay datos por corregir: están marcados en cada paso.', 'error', 6000)
    } else avisarError(e)
  } finally { ocupado.value = false }
}

function empezarDeNuevo() {
  descartarBorrador()
  Object.assign(b, nuevoBorrador())
  esquema.value = null
  errores.value = []
  recuperado.value = false
}
function cerrar() {
  router.push('/productos/catalogo')
}
</script>

<template>
  <Asistente :documento="b.producto.nombre || 'Nuevo producto'" :pasos="pasos" :actual="actual" :ocupado="ocupado" :guardado="guardado"
             texto-final="Crear producto" @ir="ir" @anterior="ir(actual - 1)" @siguiente="siguiente" @guardar="guardarBorrador(b); avisar('Borrador guardado en este navegador.', 'info')"
             @finalizar="crear" @cerrar="cerrar">
    <div v-if="recuperado" class="nota info">
      <Icono nombre="historial" :tam="16" />
      <span class="crece">Siguió con el borrador que dejó pendiente. Todo lo que escribe se guarda solo en este navegador.</span>
      <button type="button" class="btn btn-chico" @click="empezarDeNuevo">Empezar de nuevo</button>
    </div>

    <div class="con-resumen">
      <div class="pila-pasos">
        <PasoTipo v-if="paso.clave === 'tipo'" :datos="datos" @elegir="elegirTipo" @creado="tipoCreado" />
        <template v-else-if="esquema">
          <PasoGeneral v-if="paso.clave === 'general'" :esquema="esquema" :datos="datos" :errores="erroresDe('general')" />
          <PasoCaracteristicas v-else-if="paso.clave === 'caracteristicas'" :esquema="esquema" :datos="datos" :errores="erroresDe('caracteristicas')" />
          <PasoVariantes v-else-if="paso.clave === 'variantes'" :esquema="esquema" :datos="datos" :combos="combos" :errores="erroresDe('variantes')" />
          <PasoEmpaque v-else-if="paso.clave === 'empaque'" :datos="datos" :errores="erroresDe('empaque')" />
          <PasoClasificacion v-else-if="paso.clave === 'clasificacion'" :errores="erroresDe('clasificacion')" />
          <PasoRevisar v-else-if="paso.clave === 'revisar'" :esquema="esquema" :datos="datos" :previa="previa" :errores="errores"
                       :pasos="pasos" :ocupado="ocupado" @ir="(clave) => ir(pasos.findIndex((p) => p.clave === clave))" @validar="validar" />
        </template>
        <p v-else-if="b.tipoId" class="ayuda">Cargando el tipo de producto…</p>
      </div>
      <ResumenAlta v-if="paso.clave !== 'tipo'" :esquema="esquema" :datos="datos" :variantes="incluidas.length"
                   :faltan="faltanObligatorios.length" @ir="(clave) => ir(pasos.findIndex((p) => p.clave === clave))" />
    </div>
  </Asistente>
</template>

<style scoped>
.pila-pasos { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.con-resumen:has(> :only-child) { grid-template-columns: minmax(0, 1fr); }
</style>
