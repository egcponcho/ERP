<script setup>
// Diálogo modal accesible: foco atrapado, Escape cierra, el fondo no se desplaza.
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import Icono from './Icono.vue'

const props = defineProps({
  titulo: { type: String, required: true },
  descripcion: { type: String, default: '' },
  ancho: { type: String, default: '520px' },
  lateral: { type: Boolean, default: false }, // panel desde la derecha (formularios largos)
})
const emit = defineEmits(['cerrar'])
const caja = ref(null)
const id = `modal-${Math.random().toString(36).slice(2, 8)}`
let anterior = null

function teclas(e) {
  if (e.key === 'Escape') { e.stopPropagation(); emit('cerrar') }
  if (e.key !== 'Tab' || !caja.value) return
  const f = [...caja.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')]
    .filter((x) => !x.disabled && x.offsetParent !== null)
  if (!f.length) return
  if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f.at(-1).focus() }
  else if (!e.shiftKey && document.activeElement === f.at(-1)) { e.preventDefault(); f[0].focus() }
}

onMounted(async () => {
  anterior = document.activeElement
  document.body.style.overflow = 'hidden'
  await nextTick()
  const primero = caja.value?.querySelector('[autofocus], input:not([type=hidden]), select, textarea')
  ;(primero || caja.value)?.focus()
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  anterior?.focus?.()
})
</script>

<template>
  <Teleport to="body">
    <div class="velo" :class="{ lateral: props.lateral }" @mousedown.self="emit('cerrar')" @keydown="teclas">
      <div ref="caja" class="caja" role="dialog" aria-modal="true" :aria-labelledby="id" tabindex="-1"
           :style="{ '--ancho': props.ancho }">
        <header class="cabeza">
          <div>
            <h2 :id="id">{{ titulo }}</h2>
            <p v-if="descripcion" class="tenue chico">{{ descripcion }}</p>
          </div>
          <button class="btn fantasma icono chico" type="button" aria-label="Cerrar" @click="emit('cerrar')">
            <Icono nombre="cerrar" />
          </button>
        </header>
        <div class="cuerpo"><slot /></div>
        <footer v-if="$slots.pie" class="pie"><slot name="pie" /></footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.velo { position: fixed; inset: 0; background: var(--velo); display: grid; place-items: center; padding: var(--e-4); z-index: 50; animation: aparecer 0.15s ease-out; }
.caja { width: min(var(--ancho), 100%); max-height: calc(100vh - 32px); display: flex; flex-direction: column; background: var(--superficie); border-radius: var(--radio-panel); box-shadow: var(--sombra-flotante); border: 1px solid var(--linea); animation: subir 0.18s ease-out; outline: none; }
.lateral { place-items: stretch end; padding: 0; }
.lateral .caja { height: 100vh; max-height: none; border-radius: 0; animation: deslizar 0.2s ease-out; }
.cabeza { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--e-3); padding: var(--e-5) var(--e-5) var(--e-4); border-bottom: 1px solid var(--linea); }
.cabeza p { margin-top: 4px; }
.cuerpo { padding: var(--e-5); overflow-y: auto; flex: 1; }
.pie { display: flex; justify-content: flex-end; gap: var(--e-2); padding: var(--e-4) var(--e-5); border-top: 1px solid var(--linea); background: var(--superficie-2); border-radius: 0 0 var(--radio-panel) var(--radio-panel); }
.lateral .pie { border-radius: 0; }
@keyframes aparecer { from { opacity: 0; } }
@keyframes subir { from { opacity: 0; transform: translateY(8px) scale(0.99); } }
@keyframes deslizar { from { transform: translateX(24px); opacity: 0; } }
</style>
