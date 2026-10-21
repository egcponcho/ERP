// Notificaciones breves (toasts) y confirmaciones, compartidas por toda la app.
import { reactive } from 'vue'

export const avisos = reactive({ lista: [], confirmacion: null })
let siguiente = 1

export function avisar(texto, tipo = 'ok', ms = 3800) {
  const id = siguiente++
  avisos.lista.push({ id, texto, tipo })
  if (ms) setTimeout(() => cerrarAviso(id), ms)
}

export function cerrarAviso(id) {
  const i = avisos.lista.findIndex((a) => a.id === id)
  if (i >= 0) avisos.lista.splice(i, 1)
}

// Muestra el mensaje de un error de la API (con la lista de problemas si la trae)
export function avisarError(e) {
  avisar(e?.message || 'Ocurrió un error inesperado.', 'error', 6000)
}

// confirmar({titulo, mensaje, accion, peligro}) → Promise<boolean>
export function confirmar(opciones) {
  return new Promise((resolver) => {
    avisos.confirmacion = { accion: 'Confirmar', peligro: false, ...opciones, resolver }
  })
}
