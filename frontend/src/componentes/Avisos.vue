<script setup>
// Avisos breves (toasts) en una región viva para lectores de pantalla.
import { avisos, cerrarAviso } from '@/nucleo/avisos.js'
import Icono from './Icono.vue'

const ICONO = { ok: 'check', error: 'alerta', info: 'info' }
</script>

<template>
  <div class="toasts" role="status" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="a in avisos.lista" :key="a.id" class="toast" :class="a.tipo">
        <Icono :nombre="ICONO[a.tipo] || 'info'" :tam="18" />
        <span class="crece">{{ a.texto }}</span>
        <button class="toast-cerrar" type="button" aria-label="Cerrar aviso" @click="cerrarAviso(a.id)"><Icono nombre="cerrar" :tam="14" /></button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* Avisos como los banners de iOS: una cápsula de material que baja desde arriba al centro */
.toasts { position: fixed; top: 12px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 70; width: min(440px, calc(100vw - 24px)); pointer-events: none; }
.toast {
  pointer-events: auto; display: flex; align-items: center; gap: 10px; padding: 10px 12px 10px 16px; border-radius: 999px; max-width: 100%;
  background: var(--flotante); backdrop-filter: blur(24px) saturate(180%); -webkit-backdrop-filter: blur(24px) saturate(180%);
  color: #fff; box-shadow: var(--sombra-flotante); font-size: 0.94rem; font-weight: 500;
}
.toast.ok > svg:first-child { color: #30d158; }
.toast.info > svg:first-child { color: #64d2ff; }
.toast.error { background: var(--toast-error); border-radius: 18px; }
.toast.error > svg:first-child { color: #ffb4ae; }
.toast-cerrar { border: 0; background: rgba(255, 255, 255, 0.14); color: inherit; cursor: pointer; width: 24px; height: 24px; border-radius: 50%; display: grid; place-items: center; flex: none; }
.toast-cerrar:hover { background: rgba(255, 255, 255, 0.24); }
.toast-enter-active, .toast-leave-active { transition: transform var(--lento) var(--resorte), opacity var(--normal); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(-24px) scale(0.92); }
</style>
