<script setup>
// Buscador de productos (combobox): escribe y elige. v-model = id del producto.
import { onMounted, ref, watch } from 'vue'
import { api } from '@/nucleo/api.js'

const props = defineProps({ modelValue: { type: Number, default: null }, id: { type: String, required: true },
                            excluir: { type: Number, default: null }, invalido: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])
const texto = ref('')
const opciones = ref([])
const abierto = ref(false)
const activo = ref(0)
let espera = null

onMounted(async () => {
  if (props.modelValue) {
    try { const p = await api.get(`/productos/${props.modelValue}`); texto.value = `${p.codigo} · ${p.nombre}` } catch { /* sin nombre */ }
  }
})

async function buscar() {
  try {
    const r = await api.get('/productos', { q: texto.value.includes(' · ') ? '' : texto.value, tamano: 8 })
    opciones.value = r.datos.filter((p) => p.id !== props.excluir)
    activo.value = 0
  } catch { opciones.value = [] }
}

watch(texto, () => {
  clearTimeout(espera)
  espera = setTimeout(buscar, 200)
})

function alEntrar() {
  abierto.value = true
  if (!opciones.value.length) buscar()
}
function alSalir() {
  setTimeout(() => (abierto.value = false), 150)
}

function elegir(p) {
  emit('update:modelValue', p.id)
  texto.value = `${p.codigo} · ${p.nombre}`
  abierto.value = false
}

function teclas(e) {
  if (e.key === 'ArrowDown') { e.preventDefault(); abierto.value = true; activo.value = Math.min(activo.value + 1, opciones.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); activo.value = Math.max(activo.value - 1, 0) }
  else if (e.key === 'Enter' && abierto.value && opciones.value[activo.value]) { e.preventDefault(); elegir(opciones.value[activo.value]) }
  else if (e.key === 'Escape') abierto.value = false
}
</script>

<template>
  <div class="selector">
    <input :id="id" v-model="texto" class="control" :class="{ invalido }" type="text" role="combobox" autocomplete="off"
           :aria-expanded="abierto" :aria-controls="`${id}-lista`" placeholder="Buscar por código o nombre…"
           @focus="alEntrar" @input="abierto = true; emit('update:modelValue', null)" @blur="alSalir" @keydown="teclas" />
    <ul v-if="abierto && opciones.length" :id="`${id}-lista`" class="lista" role="listbox">
      <li v-for="(p, i) in opciones" :key="p.id" role="option" :aria-selected="i === activo" :class="{ activo: i === activo }"
          @mousedown.prevent="elegir(p)" @mouseenter="activo = i">
        <span class="mono">{{ p.codigo }}</span><span class="crece">{{ p.nombre }}</span><span class="tenue chico">{{ p.tipo }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.selector { position: relative; }
.lista { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; right: 0; margin: 0; padding: 4px; list-style: none; background: var(--superficie); border: 1px solid var(--linea); border-radius: var(--radio); box-shadow: var(--sombra-media); max-height: 260px; overflow-y: auto; }
li { display: flex; gap: var(--e-3); align-items: center; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-size: 13.5px; }
li.activo { background: var(--acento-claro); }
</style>
