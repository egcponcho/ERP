<script setup>
// Formulario de los datos generales de un tipo de producto (alta y edición).
import { computed, reactive, ref } from 'vue'
import Campo from '@/componentes/Campo.vue'
import Modal from '@/componentes/Modal.vue'

const props = defineProps({
  datos: { type: Object, required: true },
  tipos: { type: Array, required: true },
  unidades: { type: Array, required: true },
  titulo: { type: String, required: true },
  guardar: { type: Function, required: true }, // async (datos) → error o nada
})
const emit = defineEmits(['cerrar'])
const d = reactive({ ...props.datos })
const errores = ref({})
const guardando = ref(false)
const codigoTocado = ref(!!props.datos.codigo)

// Un tipo no puede tener como padre a sí mismo ni a uno de sus descendientes
const padres = computed(() => {
  if (!d.id) return props.tipos
  const excluir = new Set([d.id])
  let cambio = true
  while (cambio) {
    cambio = false
    for (const t of props.tipos) if (t.padre_id && excluir.has(t.padre_id) && !excluir.has(t.id)) { excluir.add(t.id); cambio = true }
  }
  return props.tipos.filter((t) => !excluir.has(t.id))
})
const ejemplo = computed(() => {
  const m = /\{seq(?::0?(\d+)d?)?\}/.exec(d.plantilla_codigo || '')
  if (!m) return ''
  return d.plantilla_codigo.replace(m[0], String(d.siguiente_numero || 1).padStart(Number(m[1] || 0), '0'))
})

function codigoDesdeNombre() {
  if (codigoTocado.value) return
  d.codigo = d.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 30)
}

async function enviar() {
  guardando.value = true
  const cuerpo = { ...d }
  for (const k of ['id', 'atributos', 'asignaciones', 'creado_en', 'actualizado_en']) delete cuerpo[k]
  for (const k of ['descripcion', 'plantilla_codigo', 'plantilla_sku']) cuerpo[k] = cuerpo[k] || null
  cuerpo.siguiente_numero = Number(cuerpo.siguiente_numero) || 1
  const error = await props.guardar(cuerpo)
  guardando.value = false
  if (error) errores.value = { ...error.porCampo, _general: error.message }
}
</script>

<template>
  <Modal :titulo="titulo" ancho="600px" @cerrar="emit('cerrar')">
    <form id="form-tipo" class="pila" @submit.prevent="enviar">
      <div v-if="errores._general" class="aviso-caja error" role="alert">{{ errores._general }}</div>
      <div class="rejilla-2">
        <Campo etiqueta="Nombre" id="t-nombre" :error="errores.nombre" obligatorio>
          <input id="t-nombre" v-model="d.nombre" class="control" required maxlength="100" placeholder="Calzado" @input="codigoDesdeNombre" />
        </Campo>
        <Campo etiqueta="Código" id="t-codigo" :error="errores.codigo" obligatorio>
          <input id="t-codigo" v-model="d.codigo" class="control mono" required maxlength="30" placeholder="CALZADO" @input="codigoTocado = true" />
        </Campo>
      </div>
      <Campo etiqueta="Descripción" id="t-desc">
        <input id="t-desc" v-model="d.descripcion" class="control" maxlength="500" />
      </Campo>
      <div class="rejilla-2">
        <Campo etiqueta="Tipo padre" id="t-padre" :error="errores.padre_id" ayuda="Hereda sus atributos, unidad y plantillas.">
          <select id="t-padre" v-model="d.padre_id" class="control">
            <option :value="null">Ninguno (tipo raíz)</option>
            <option v-for="t in padres" :key="t.id" :value="t.id">{{ t.nombre }}</option>
          </select>
        </Campo>
        <Campo etiqueta="Unidad base por defecto" id="t-unidad" :error="errores.unidad_defecto_id">
          <select id="t-unidad" v-model="d.unidad_defecto_id" class="control">
            <option :value="null">{{ d.padre_id ? 'La del tipo padre' : 'Ninguna' }}</option>
            <option v-for="u in unidades" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
          </select>
        </Campo>
      </div>
      <div class="rejilla-2">
        <Campo etiqueta="Numeración de productos" id="t-plantilla" :error="errores.plantilla_codigo"
               :ayuda="ejemplo ? `El próximo será ${ejemplo}` : 'Ejemplo: CAL-{seq:05}. Vacío: el código se escribe a mano.'">
          <input id="t-plantilla" v-model="d.plantilla_codigo" class="control mono" maxlength="60" placeholder="CAL-{seq:05}" />
        </Campo>
        <Campo etiqueta="Siguiente número" id="t-sig">
          <input id="t-sig" v-model="d.siguiente_numero" class="control num" type="number" min="1" />
        </Campo>
      </div>
      <Campo etiqueta="Código de las variantes (SKU)" id="t-sku" :error="errores.plantilla_sku"
             ayuda="Use {producto} y los códigos de los atributos eje: {producto}-{color}-{talla}. Vacío: código del producto + valores de los ejes.">
        <input id="t-sku" v-model="d.plantilla_sku" class="control mono" maxlength="120" placeholder="{producto}-{color}-{talla}" />
      </Campo>
      <label class="interruptor"><input v-model="d.activo" type="checkbox" />Activo</label>
    </form>
    <template #pie>
      <button class="btn" type="button" @click="emit('cerrar')">Cancelar</button>
      <button class="btn primario" type="submit" form="form-tipo" :disabled="guardando"><span v-if="guardando" class="cargando-btn" />Guardar</button>
    </template>
  </Modal>
</template>
