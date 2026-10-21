<script setup>
// Toasts (región viva para lectores de pantalla) y el diálogo de confirmación.
import { avisos, cerrarAviso } from '@/nucleo/avisos.js'
import Icono from './Icono.vue'
import Modal from './Modal.vue'

const ICONO = { ok: 'check', error: 'alerta', info: 'info' }

function responder(si) {
  const c = avisos.confirmacion
  avisos.confirmacion = null
  c?.resolver(si)
}
</script>

<template>
  <div class="toasts" role="status" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="a in avisos.lista" :key="a.id" class="toast" :class="a.tipo">
        <Icono :nombre="ICONO[a.tipo] || 'info'" />
        <span class="crece">{{ a.texto }}</span>
        <button class="cerrar" type="button" aria-label="Cerrar aviso" @click="cerrarAviso(a.id)"><Icono nombre="cerrar" :tam="14" /></button>
      </div>
    </TransitionGroup>
  </div>
  <Modal v-if="avisos.confirmacion" :titulo="avisos.confirmacion.titulo" ancho="440px" @cerrar="responder(false)">
    <p class="tenue">{{ avisos.confirmacion.mensaje }}</p>
    <template #pie>
      <button class="btn" type="button" @click="responder(false)">Cancelar</button>
      <button class="btn" :class="avisos.confirmacion.peligro ? 'peligro lleno' : 'primario'" type="button" autofocus
              @click="responder(true)">{{ avisos.confirmacion.accion }}</button>
    </template>
  </Modal>
</template>

<style scoped>
.toasts { position: fixed; right: var(--e-5); bottom: var(--e-5); display: flex; flex-direction: column; gap: var(--e-2); z-index: 60; width: min(380px, calc(100vw - 32px)); }
.toast { display: flex; align-items: flex-start; gap: var(--e-3); padding: var(--e-3) var(--e-4); border-radius: var(--radio); background: #0f1d33; color: #e6ebf3; box-shadow: var(--sombra-flotante); font-size: 13.5px; }
.toast.ok :first-child { color: #4ccf86; }
.toast.error { background: #7f1d18; }
.toast.error :first-child { color: #ffb4ae; }
.cerrar { border: 0; background: transparent; color: inherit; opacity: 0.7; cursor: pointer; padding: 2px; border-radius: 4px; }
.cerrar:hover { opacity: 1; }
.toast-enter-active, .toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
</style>
