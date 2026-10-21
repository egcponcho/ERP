<script setup>
// Un tipo de producto: sus datos y los atributos que se capturan en sus productos
// (propios y heredados), con una vista previa del formulario que resulta.
import { computed, onMounted, ref } from 'vue'
import { api, CONFIG } from '@/nucleo/api.js'
import { avisar, avisarError, confirmar } from '@/nucleo/avisos.js'
import { catalogo, invalidarCatalogo } from '@/nucleo/catalogos.js'
import { TIPOS_DATO, valorTexto } from '@/nucleo/formato.js'
import Campo from '@/componentes/Campo.vue'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'
import FormTipo from './FormTipo.vue'

const props = defineProps({ id: { type: Number, required: true } })
const tipo = ref(null)
const esquema = ref(null)
const tipos = ref([])
const unidades = ref([])
const atributos = ref([])
const editandoTipo = ref(false)
const asignando = ref(null) // {nuevo, datos}
const errores = ref({})
const guardando = ref(false)
const previa = ref({})

async function cargar() {
  try {
    ;[tipo.value, esquema.value, tipos.value, unidades.value, atributos.value] = await Promise.all([
      api.get(`${CONFIG}/tipos-producto/${props.id}`), api.get(`${CONFIG}/tipos-producto/${props.id}/esquema`),
      catalogo('tipos-producto', { recargar: true }), catalogo('unidades'), catalogo('atributos', { recargar: true })])
  } catch (e) { avisarError(e) }
}
onMounted(cargar)

const propias = computed(() => new Map((tipo.value?.asignaciones || []).map((a) => [a.atributo_id, a])))
const ocultos = computed(() => (tipo.value?.asignaciones || []).filter((a) => a.oculto)
  .map((a) => ({ ...a, atributo: atributos.value.find((x) => x.id === a.atributo_id) })))
const campos = (nivel) => (esquema.value?.campos || []).filter((c) => c.nivel === nivel)
const disponibles = computed(() => {
  const usados = new Set((esquema.value?.campos || []).map((c) => c.atributo.id))
  for (const a of tipo.value?.asignaciones || []) usados.add(a.atributo_id)
  return atributos.value.filter((a) => a.activo && !usados.has(a.id))
})
const ruta = computed(() => (esquema.value?.ruta || []).map((c) => tipos.value.find((t) => t.codigo === c)).filter(Boolean))
const unidadNombre = computed(() => {
  const id = esquema.value?.unidad_defecto_id
  const u = unidades.value.find((x) => x.id === id)
  return u ? `${u.nombre} (${u.codigo})` : 'Sin definir'
})
const atributoElegido = computed(() => atributos.value.find((a) => a.id === asignando.value?.datos.atributo_id))

async function guardarTipo(datos) {
  try {
    await api.patch(`${CONFIG}/tipos-producto/${props.id}`, datos)
    invalidarCatalogo('tipos-producto')
    avisar('Tipo guardado.')
    editandoTipo.value = false
    await cargar()
  } catch (e) { return e }
}

function nuevaAsignacion() {
  errores.value = {}
  asignando.value = { nuevo: true, datos: { atributo_id: null, nivel: 'producto', es_eje: false, obligatorio: false, oculto: false, valor_defecto: null, orden: 0 } }
}
function editarAsignacion(c) {
  errores.value = {}
  const propia = propias.value.get(c.atributo.id)
  asignando.value = {
    nuevo: !propia, heredada: !!c.heredado_de, origen: c.heredado_de,
    datos: { atributo_id: c.atributo.id, nivel: c.nivel, es_eje: c.es_eje, obligatorio: c.obligatorio, oculto: false, valor_defecto: c.valor_defecto, orden: c.orden },
  }
}

async function guardarAsignacion() {
  guardando.value = true
  errores.value = {}
  const d = { ...asignando.value.datos }
  if (d.es_eje) { d.nivel = 'variante'; d.valor_defecto = null }
  try {
    if (asignando.value.nuevo) await api.post(`${CONFIG}/tipos-producto/${props.id}/atributos`, d)
    else await api.patch(`${CONFIG}/tipos-producto/${props.id}/atributos/${d.atributo_id}`, d)
    avisar('Atributo del tipo guardado.')
    asignando.value = null
    await cargar()
  } catch (e) {
    errores.value = { ...e.porCampo, _general: e.message }
  } finally { guardando.value = false }
}

async function quitar(c) {
  const heredada = !!c.heredado_de
  const ok = await confirmar(heredada
    ? { titulo: 'Ocultar atributo heredado', mensaje: `«${c.atributo.nombre}» viene del tipo ${c.heredado_de}. Se ocultará solo en este tipo y sus subtipos; los valores ya capturados se conservan.`, accion: 'Ocultar' }
    : { titulo: 'Quitar atributo', mensaje: `Se quitará «${c.atributo.nombre}» de este tipo. Si ya hay valores capturados no se podrá: en ese caso ocúltelo.`, accion: 'Quitar', peligro: true })
  if (!ok) return
  try {
    if (heredada) {
      const propia = propias.value.get(c.atributo.id)
      if (propia) await api.patch(`${CONFIG}/tipos-producto/${props.id}/atributos/${c.atributo.id}`, { oculto: true })
      else await api.post(`${CONFIG}/tipos-producto/${props.id}/atributos`, { atributo_id: c.atributo.id, nivel: c.nivel, es_eje: c.es_eje, oculto: true })
    } else await api.del(`${CONFIG}/tipos-producto/${props.id}/atributos/${c.atributo.id}`)
    avisar(heredada ? 'Atributo oculto en este tipo.' : 'Atributo quitado.')
    await cargar()
  } catch (e) { avisarError(e) }
}

async function mostrar(a) {
  try {
    await api.del(`${CONFIG}/tipos-producto/${props.id}/atributos/${a.atributo_id}`)
    avisar('El atributo vuelve a mostrarse.')
    await cargar()
  } catch (e) { avisarError(e) }
}

async function restablecer(c) {
  try {
    await api.del(`${CONFIG}/tipos-producto/${props.id}/atributos/${c.atributo.id}`)
    avisar('Se usa otra vez la configuración heredada.')
    await cargar()
  } catch (e) { avisarError(e) }
}
</script>

<template>
  <div class="pagina">
    <template v-if="tipo && esquema">
      <header class="pagina-cabeza">
        <div>
          <nav class="migas" aria-label="Ruta">
            <RouterLink to="/configuracion/tipos">Tipos de producto</RouterLink>
            <template v-for="t in ruta.slice(0, -1)" :key="t.id"><Icono nombre="derecha" :tam="12" /><RouterLink :to="`/configuracion/tipos/${t.id}`">{{ t.nombre }}</RouterLink></template>
          </nav>
          <div class="fila"><h1>{{ tipo.nombre }}</h1><code class="tenue">{{ tipo.codigo }}</code>
            <span v-if="!tipo.activo" class="insignia">Inactivo</span></div>
          <p>{{ tipo.descripcion || 'Configure qué se captura en los productos de este tipo.' }}</p>
        </div>
        <button class="btn" type="button" @click="editandoTipo = true"><Icono nombre="editar" :tam="16" />Editar datos</button>
      </header>

      <section class="resumen">
        <div><span class="tenue chico">Unidad base</span><strong>{{ unidadNombre }}</strong></div>
        <div><span class="tenue chico">Numeración</span><strong class="mono">{{ tipo.plantilla_codigo || (tipo.padre_id ? 'Heredada' : 'Manual') }}</strong></div>
        <div><span class="tenue chico">SKU de variantes</span><strong class="mono">{{ esquema.plantilla_sku || 'Automático' }}</strong></div>
        <div><span class="tenue chico">Ejes de variante</span><strong>{{ esquema.campos.filter((c) => c.es_eje).map((c) => c.atributo.nombre).join(', ') || 'Sin variantes' }}</strong></div>
      </section>

      <div class="dos-columnas">
        <section class="tarjeta">
          <header class="tarjeta-cabeza">
            <div><h2>Atributos</h2><p>Lo que se captura en cada producto y en cada variante.</p></div>
            <button class="btn primario" type="button" :disabled="!disponibles.length" @click="nuevaAsignacion"><Icono nombre="mas" :tam="16" />Asignar atributo</button>
          </header>
          <template v-for="nivel in ['producto', 'variante']" :key="nivel">
            <h3 class="nivel">{{ nivel === 'producto' ? 'Del producto' : 'De cada variante' }}
              <span class="tenue chico">{{ nivel === 'producto' ? 'Lo comparten todas sus variantes' : 'Los ejes distinguen una variante de otra' }}</span></h3>
            <div class="tabla-envoltura">
              <table v-if="campos(nivel).length" class="tabla">
                <thead><tr><th>Atributo</th><th>Tipo de dato</th><th>Reglas</th><th>Valor por defecto</th><th>Origen</th><th class="acciones"><span class="solo-lector">Acciones</span></th></tr></thead>
                <tbody>
                  <tr v-for="c in campos(nivel)" :key="c.atributo.id">
                    <td><strong class="nombre">{{ c.atributo.nombre }}</strong> <code class="tenue">{{ c.atributo.codigo }}</code></td>
                    <td class="tenue">{{ TIPOS_DATO[c.atributo.tipo_dato] }}</td>
                    <td><div class="fila envolver">
                      <span v-if="c.es_eje" class="insignia sin-punto acento">Eje de variante</span>
                      <span v-if="c.obligatorio" class="insignia sin-punto aviso">Obligatorio</span>
                      <span v-if="!c.es_eje && !c.obligatorio" class="tenue">Opcional</span>
                    </div></td>
                    <td>{{ valorTexto(c.valor_defecto, c.atributo) }}</td>
                    <td>
                      <span v-if="c.heredado_de" class="origen"><Icono nombre="heredado" :tam="13" />{{ c.heredado_de }}<template v-if="propias.has(c.atributo.id)"> · cambiado aquí</template></span>
                      <span v-else class="tenue">Propio</span>
                    </td>
                    <td class="acciones">
                      <button class="btn fantasma icono chico" type="button" :aria-label="`Editar ${c.atributo.nombre}`" :title="c.heredado_de ? 'Cambiar solo en este tipo' : 'Editar'" @click="editarAsignacion(c)"><Icono nombre="editar" :tam="16" /></button>
                      <button v-if="c.heredado_de && propias.has(c.atributo.id)" class="btn fantasma icono chico" type="button" title="Volver a lo heredado" :aria-label="`Restablecer ${c.atributo.nombre}`" @click="restablecer(c)"><Icono nombre="historial" :tam="16" /></button>
                      <button class="btn fantasma icono chico peligro" type="button" :title="c.heredado_de ? 'Ocultar en este tipo' : 'Quitar'" :aria-label="`${c.heredado_de ? 'Ocultar' : 'Quitar'} ${c.atributo.nombre}`" @click="quitar(c)"><Icono :nombre="c.heredado_de ? 'ojoNo' : 'borrar'" :tam="16" /></button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="tenue vacio-nivel">{{ nivel === 'producto' ? 'Sin atributos del producto.' : 'Sin atributos de variante: los productos de este tipo no tienen variantes.' }}</p>
            </div>
          </template>
          <div v-if="ocultos.length" class="ocultos">
            <span class="tenue chico">Ocultos en este tipo:</span>
            <span v-for="a in ocultos" :key="a.atributo_id" class="chip">{{ a.atributo?.nombre }}
              <button type="button" :aria-label="`Mostrar ${a.atributo?.nombre}`" title="Mostrar otra vez" @click="mostrar(a)"><Icono nombre="ojo" :tam="13" /></button></span>
          </div>
          <EstadoVacio v-if="!esquema.campos.length && !atributos.length" icono="etiqueta" titulo="Primero cree atributos"
                       texto="Los atributos se definen una vez en Configuración → Atributos y luego se asignan aquí.">
            <RouterLink class="btn primario" to="/configuracion/atributos">Ir a atributos</RouterLink>
          </EstadoVacio>
        </section>

        <aside class="tarjeta previa">
          <header class="tarjeta-cabeza"><div><h2>Vista previa</h2><p>Así se verá la ficha de un producto de este tipo.</p></div></header>
          <div class="tarjeta-cuerpo pila">
            <CampoAtributo v-for="c in campos('producto')" :key="c.atributo.id" v-model="previa[c.atributo.codigo]" :campo="c" :unidades="unidades" id-base="previa" />
            <p v-if="!campos('producto').length" class="tenue chico">Sin atributos del producto.</p>
            <template v-if="campos('variante').length">
              <h3 class="sub">Cada variante</h3>
              <CampoAtributo v-for="c in campos('variante')" :key="c.atributo.id" v-model="previa[`v_${c.atributo.codigo}`]" :campo="c" :unidades="unidades" id-base="previa-v" />
            </template>
          </div>
        </aside>
      </div>
    </template>
    <div v-else class="pila"><span class="esqueleto" style="width: 240px; height: 24px" /><span class="esqueleto" style="height: 120px" /></div>

    <FormTipo v-if="editandoTipo" :datos="tipo" :tipos="tipos" :unidades="unidades" :titulo="`Editar ${tipo.nombre}`"
              :guardar="guardarTipo" @cerrar="editandoTipo = false" />

    <Modal v-if="asignando" :titulo="asignando.heredada ? 'Cambiar atributo heredado' : asignando.nuevo ? 'Asignar atributo' : 'Editar atributo del tipo'"
           :descripcion="asignando.heredada ? `Viene del tipo ${asignando.origen}. El cambio aplica solo a este tipo y sus subtipos.` : ''"
           ancho="520px" @cerrar="asignando = null">
      <form id="form-asignacion" class="pila" @submit.prevent="guardarAsignacion">
        <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
        <Campo etiqueta="Atributo" id="as-atributo" obligatorio>
          <select v-if="asignando.nuevo && !asignando.heredada" id="as-atributo" v-model="asignando.datos.atributo_id" class="control" required>
            <option :value="null" disabled>Elegir…</option>
            <option v-for="a in disponibles" :key="a.id" :value="a.id">{{ a.nombre }} · {{ TIPOS_DATO[a.tipo_dato] }}</option>
          </select>
          <input v-else id="as-atributo" class="control" :value="atributoElegido?.nombre" disabled />
        </Campo>
        <fieldset class="niveles">
          <legend class="etiqueta">Se captura en</legend>
          <label class="nivel-op" :class="{ elegido: asignando.datos.nivel === 'producto' }">
            <input v-model="asignando.datos.nivel" type="radio" value="producto" @change="asignando.datos.es_eje = false" />
            <strong>El producto</strong><span>Un solo valor para todas sus variantes (material, marca, pureza).</span>
          </label>
          <label class="nivel-op" :class="{ elegido: asignando.datos.nivel === 'variante' }">
            <input v-model="asignando.datos.nivel" type="radio" value="variante" />
            <strong>Cada variante</strong><span>Puede cambiar de una variante a otra (talla, color, voltaje).</span>
          </label>
        </fieldset>
        <label v-if="asignando.datos.nivel === 'variante'" class="pila-chica">
          <span class="interruptor"><input v-model="asignando.datos.es_eje" type="checkbox" :disabled="atributoElegido?.tipo_dato === 'opciones'" />Distingue variantes (eje)</span>
          <span class="tenue chico">Cada combinación de ejes es un SKU distinto. Los ejes siempre son obligatorios.</span>
        </label>
        <label v-if="!asignando.datos.es_eje" class="interruptor"><input v-model="asignando.datos.obligatorio" type="checkbox" />Obligatorio para la ficha completa</label>
        <div v-if="atributoElegido && !asignando.datos.es_eje" class="defecto">
          <p class="etiqueta">Valor por defecto <span class="tenue">(opcional, para los productos nuevos)</span></p>
          <CampoAtributo v-model="asignando.datos.valor_defecto" :campo="{ atributo: atributoElegido, obligatorio: false }"
                         :unidades="unidades" id-base="defecto" :error="errores.valor_defecto" />
        </div>
        <Campo etiqueta="Orden" id="as-orden"><input id="as-orden" v-model.number="asignando.datos.orden" class="control num" type="number" /></Campo>
      </form>
      <template #pie>
        <button class="btn" type="button" @click="asignando = null">Cancelar</button>
        <button class="btn primario" type="submit" form="form-asignacion" :disabled="guardando || !asignando.datos.atributo_id"><span v-if="guardando" class="cargando-btn" />Guardar</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.resumen { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1px; background: var(--linea); border: 1px solid var(--linea); border-radius: var(--radio-panel); overflow: hidden; }
.resumen > div { background: var(--superficie); padding: var(--e-4) var(--e-5); display: flex; flex-direction: column; gap: 2px; }
.resumen strong { font-weight: 600; }
.dos-columnas { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: var(--e-5); align-items: start; }
@media (max-width: 1100px) { .dos-columnas { grid-template-columns: 1fr; } }
.nivel { padding: var(--e-4) var(--e-5) var(--e-2); display: flex; align-items: baseline; gap: var(--e-2); }
.vacio-nivel { padding: 0 var(--e-5) var(--e-4); font-size: 13px; }
.nombre { font-weight: 550; }
.origen { display: inline-flex; align-items: center; gap: 4px; color: var(--tinta-3); font-size: 13px; }
.ocultos { display: flex; flex-wrap: wrap; align-items: center; gap: var(--e-2); padding: var(--e-3) var(--e-5) var(--e-4); border-top: 1px solid var(--linea-suave); }
.previa { position: sticky; top: var(--e-5); }
.sub { padding-top: var(--e-2); border-top: 1px solid var(--linea-suave); }
.niveles { border: 0; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: var(--e-2); }
.niveles legend { margin-bottom: var(--e-2); }
.nivel-op { display: flex; flex-direction: column; gap: 2px; padding: var(--e-3); border: 1px solid var(--borde-control); border-radius: var(--radio); cursor: pointer; position: relative; }
.nivel-op input { position: absolute; opacity: 0; }
.nivel-op span { font-size: 12px; color: var(--tinta-3); }
.nivel-op.elegido { border-color: var(--acento); background: var(--acento-claro); box-shadow: 0 0 0 1px var(--acento); }
.nivel-op:has(input:focus-visible) { outline: 2px solid var(--acento); outline-offset: 2px; }
.defecto { display: flex; flex-direction: column; gap: var(--e-2); padding: var(--e-3); border-radius: var(--radio); background: var(--superficie-2); border: 1px dashed var(--borde-control); }
</style>
