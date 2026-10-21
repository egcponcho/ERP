<script setup>
// Alta de producto en dos pasos: elegir el tipo y llenar la ficha que ese tipo define.
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError } from '@/nucleo/avisos.js'
import { catalogo } from '@/nucleo/catalogos.js'
import Campo from '@/componentes/Campo.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import SelectorCategorias from './SelectorCategorias.vue'

const emit = defineEmits(['cerrar'])
const router = useRouter()
const tipos = ref(null)
const unidades = ref([])
const busqueda = ref('')
const esquema = ref(null)
const f = reactive({ nombre: '', codigo: '', descripcion: '', unidad_id: null, atributos: {}, categorias: [] })
const errores = ref({})
const general = ref(null)
const guardando = ref(false)

onMounted(async () => {
  try {
    ;[tipos.value, unidades.value] = await Promise.all([catalogo('tipos-producto', { recargar: true }), catalogo('unidades')])
  } catch (e) { avisarError(e); tipos.value = [] }
})

const rutaTipo = (t) => {
  const r = []
  let x = t
  while (x) { r.unshift(x.nombre); x = tipos.value.find((p) => p.id === x.padre_id) }
  return r.join(' › ')
}
const visibles = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return (tipos.value || []).filter((t) => t.activo && (!q || rutaTipo(t).toLowerCase().includes(q)))
    .sort((a, b) => rutaTipo(a).localeCompare(rutaTipo(b)))
})
const camposProducto = computed(() => (esquema.value?.campos || []).filter((c) => c.nivel === 'producto'))
const tieneVariantes = computed(() => (esquema.value?.campos || []).some((c) => c.es_eje))
const tipoElegido = computed(() => tipos.value?.find((t) => t.id === esquema.value?.tipo.id))
const numeracion = computed(() => {
  let t = tipoElegido.value
  while (t && !t.plantilla_codigo) t = tipos.value.find((p) => p.id === t.padre_id)
  return t?.plantilla_codigo
})

async function elegir(t) {
  try {
    esquema.value = await api.get(`${CONFIG}/tipos-producto/${t.id}/esquema`)
    f.unidad_id = esquema.value.unidad_defecto_id
    f.atributos = {}
    for (const c of camposProducto.value) if (c.valor_defecto !== null && c.valor_defecto !== undefined) f.atributos[c.atributo.codigo] = c.valor_defecto
  } catch (e) { avisarError(e) }
}

async function crear() {
  guardando.value = true
  errores.value = {}
  general.value = null
  const atributos = Object.fromEntries(Object.entries(f.atributos).filter(([, v]) => v !== null && v !== '' && !(Array.isArray(v) && !v.length)))
  try {
    const p = await api.post('/productos', { tipo_id: esquema.value.tipo.id, nombre: f.nombre, codigo: f.codigo || null,
      descripcion: f.descripcion || null, unidad_id: f.unidad_id, atributos, categorias: f.categorias })
    avisar(`Se creó ${p.codigo} · ${p.nombre}.`)
    router.push(`/productos/${p.id}`)
  } catch (e) {
    errores.value = e.porCampo
    general.value = e
  } finally { guardando.value = false }
}
</script>

<template>
  <Modal :titulo="esquema ? `Nuevo producto · ${esquema.tipo.nombre}` : 'Nuevo producto'" lateral ancho="620px"
         :descripcion="esquema ? 'Los campos salen de la configuración del tipo.' : 'Paso 1 de 2 · Elija el tipo de producto.'" @cerrar="emit('cerrar')">
    <div v-if="!esquema" class="pila">
      <div class="busqueda">
        <Icono nombre="buscar" :tam="16" />
        <input v-model="busqueda" class="control" type="search" placeholder="Buscar tipo" aria-label="Buscar tipo de producto" autofocus />
      </div>
      <div v-if="visibles.length" class="tipos" role="list">
        <button v-for="t in visibles" :key="t.id" type="button" class="tipo" role="listitem" @click="elegir(t)">
          <span class="icono-tipo"><Icono nombre="capas" :tam="18" /></span>
          <span class="crece"><strong>{{ t.nombre }}</strong><span class="tenue chico">{{ rutaTipo(t) }}</span></span>
          <Icono nombre="derecha" :tam="16" class="tenue" />
        </button>
      </div>
      <EstadoVacio v-else-if="tipos && !tipos.length" icono="capas" titulo="Aún no hay tipos de producto"
                   texto="Antes de crear productos, defina al menos un tipo con sus atributos.">
        <RouterLink class="btn primario" to="/configuracion/tipos" @click="emit('cerrar')">Crear un tipo</RouterLink>
      </EstadoVacio>
      <p v-else-if="tipos" class="tenue">Ningún tipo coincide con «{{ busqueda }}».</p>
    </div>

    <form v-else id="form-producto" class="pila" novalidate @submit.prevent="crear">
      <button type="button" class="btn fantasma chico volver" @click="esquema = null"><Icono nombre="izquierda" :tam="14" />Cambiar tipo</button>
      <div v-if="general" class="aviso-caja error" role="alert">
        <Icono nombre="alerta" />
        <div>{{ general.message }}
          <ul v-if="general.detalle?.faltantes"><li v-for="x in general.detalle.faltantes" :key="x.atributo || x.taxonomia">{{ x.nombre }}</li></ul>
        </div>
      </div>

      <section class="pila">
        <h3>Datos generales</h3>
        <Campo etiqueta="Nombre" id="p-nombre" :error="errores.nombre" obligatorio>
          <input id="p-nombre" v-model="f.nombre" class="control" maxlength="200" required autofocus />
        </Campo>
        <div class="rejilla-2">
          <Campo etiqueta="Código" id="p-codigo" :error="errores.codigo" :obligatorio="!numeracion"
                 :ayuda="numeracion ? `Vacío: se genera con ${numeracion}` : 'El tipo no tiene numeración automática.'">
            <input id="p-codigo" v-model="f.codigo" class="control mono" maxlength="60" :placeholder="numeracion ? 'Automático' : ''" />
          </Campo>
          <Campo etiqueta="Unidad base" id="p-unidad" :error="errores.unidad_id" obligatorio>
            <select id="p-unidad" v-model="f.unidad_id" class="control">
              <option :value="null" disabled>Elegir…</option>
              <option v-for="u in unidades.filter((x) => x.activa)" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
            </select>
          </Campo>
        </div>
        <Campo etiqueta="Descripción" id="p-desc"><textarea id="p-desc" v-model="f.descripcion" class="control" rows="2" /></Campo>
      </section>

      <section v-if="camposProducto.length" class="pila">
        <h3>Características</h3>
        <div class="rejilla-2">
          <CampoAtributo v-for="c in camposProducto" :key="c.atributo.id" v-model="f.atributos[c.atributo.codigo]" :campo="c"
                         :unidades="unidades" :error="errores[`atributos.${c.atributo.codigo}`]" id-base="nuevo" />
        </div>
      </section>

      <section class="pila">
        <h3>Categorías</h3>
        <SelectorCategorias v-model="f.categorias" />
      </section>

      <div v-if="tieneVariantes" class="aviso-caja info"><Icono nombre="info" />
        <span>Este tipo maneja variantes ({{ esquema.campos.filter((c) => c.es_eje).map((c) => c.atributo.nombre).join(', ') }}). Las crea después de guardar, en la pestaña Variantes.</span>
      </div>
    </form>

    <template v-if="esquema" #pie>
      <button class="btn" type="button" @click="emit('cerrar')">Cancelar</button>
      <button class="btn primario" type="submit" form="form-producto" :disabled="guardando || !f.nombre.trim()"><span v-if="guardando" class="cargando-btn" />Crear producto</button>
    </template>
  </Modal>
</template>

<style scoped>
.busqueda { position: relative; }
.busqueda svg { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--tinta-3); pointer-events: none; }
.busqueda .control { padding-left: 32px; }
.tipos { display: flex; flex-direction: column; gap: var(--e-2); }
.tipo { display: flex; align-items: center; gap: var(--e-3); padding: var(--e-3) var(--e-4); border: 1px solid var(--linea); border-radius: var(--radio); background: var(--superficie); cursor: pointer; text-align: left; font: inherit; color: var(--tinta); transition: border-color 0.15s, background-color 0.15s; }
.tipo:hover { border-color: var(--acento); background: var(--acento-claro); }
.tipo strong { display: block; font-weight: 600; }
.icono-tipo { width: 36px; height: 36px; border-radius: 9px; display: grid; place-items: center; background: var(--acento-claro); color: var(--acento-texto); }
.volver { align-self: flex-start; margin: calc(var(--e-2) * -1) 0 0 calc(var(--e-3) * -1); }
h3 { color: var(--tinta-2); }
section + section { padding-top: var(--e-4); border-top: 1px solid var(--linea-suave); }
</style>
