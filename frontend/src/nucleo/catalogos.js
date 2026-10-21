// Catálogos de configuración que usan varias pantallas (unidades, estados, tipos…),
// leídos una vez y vueltos a leer cuando se modifican.
import { reactive } from 'vue'
import { api, CONFIG } from './api.js'

const cache = reactive({})
const pendientes = {}

export async function catalogo(ruta, { recargar = false } = {}) {
  if (!recargar && cache[ruta]) return cache[ruta]
  if (!recargar && pendientes[ruta]) return pendientes[ruta]
  pendientes[ruta] = api.get(`${CONFIG}/${ruta}`).then((datos) => {
    cache[ruta] = datos
    delete pendientes[ruta]
    return datos
  }).catch((e) => { delete pendientes[ruta]; throw e })
  return pendientes[ruta]
}

export function invalidarCatalogo(ruta) {
  delete cache[ruta]
}
