// Borrador del asistente de alta: se guarda en este navegador a cada cambio, así
// se puede cerrar la pestaña y seguir después donde se quedó.
import { reactive } from 'vue'

const CLAVE = 'erp.asistente-producto'

export function nuevoBorrador() {
  return {
    paso: 0,
    tipoId: null,
    producto: { nombre: '', codigo: '', descripcion: '', unidad_id: null, atributos: {}, categorias: [] },
    ejes: {}, // {codigo del eje: [valores]}
    comunes: {}, // valores de los atributos de variante que no son eje, iguales para todas
    excluidas: [], // combinaciones que la persona quitó
    presentaciones: [],
    identificadores: [],
    estadoId: null,
    guardadoEn: null,
  }
}

export function cargarBorrador() {
  try {
    const x = JSON.parse(localStorage.getItem(CLAVE))
    return x ? { ...nuevoBorrador(), ...x, producto: { ...nuevoBorrador().producto, ...x.producto } } : null
  } catch { return null }
}

export function guardarBorrador(b) {
  try {
    b.guardadoEn = new Date().toISOString()
    localStorage.setItem(CLAVE, JSON.stringify(b))
  } catch { /* sin almacenamiento: el borrador dura mientras la página esté abierta */ }
}

export function descartarBorrador() {
  try { localStorage.removeItem(CLAVE) } catch { /* nada que borrar */ }
}

// Combinaciones de los valores de los ejes, en el orden de los ejes
export function combinaciones(ejes, valores) {
  let res = [{}]
  for (const e of ejes) {
    const vs = valores[e.atributo.codigo] || []
    res = res.flatMap((c) => vs.map((v) => ({ ...c, [e.atributo.codigo]: v })))
  }
  return ejes.length ? res.filter((c) => Object.keys(c).length === ejes.length) : []
}

export const claveCombinacion = (c) => JSON.stringify(c)

// El borrador en curso, compartido por el asistente y sus pasos
export const b = reactive(nuevoBorrador())
