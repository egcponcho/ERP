// Registro de módulos de la interfaz.
//
// Cada carpeta src/modulos/<clave>/ trae un modulo.js que exporta su contrato:
//   { clave, nombre, icono, ruta, accion?, apartados?, inicio?, rutas }
// El marco (menú, barra de pestañas del celular, Inicio y rutas) se arma solo
// con estos contratos: agregar un módulo es agregar su carpeta, sin tocar el marco.
//
// El servidor dice qué módulos están activos (GET /api/modulos, según la
// variable MODULOS). Un módulo apagado en el servidor no aparece aquí.
//
// Regla de independencia (la revisa `npm run lint`): un módulo solo importa de
// src/nucleo, src/componentes y de su propia carpeta, nunca de otro módulo.
import { computed, ref } from 'vue'
import { api } from './api.js'

const CONTRATOS = import.meta.glob('../modulos/*/modulo.js', { eager: true })

export const MODULOS = Object.values(CONTRATOS).map((m) => m.default)

// null mientras no responde el servidor: se muestran todos para no parpadear
const claves = ref(null)

export const modulosActivos = computed(() => (claves.value ? MODULOS.filter((m) => claves.value.includes(m.clave)) : MODULOS))

export const moduloDe = (clave) => MODULOS.find((m) => m.clave === clave)

export async function cargarModulosActivos() {
  try {
    claves.value = (await api.get('/modulos')).map((m) => m.clave)
  } catch {
    claves.value = null // sin servidor: se muestra todo y cada pantalla avisa su error
  }
}

export const estaActivo = (clave) => !claves.value || claves.value.includes(clave)
