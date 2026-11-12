// Revisa que los módulos de la interfaz sean independientes (se corre con `npm run lint`):
// - src/modulos/<clave>/ solo importa de src/nucleo, src/componentes y de sí mismo.
// - src/nucleo y src/componentes no importan ningún módulo.
// - Cada módulo tiene su contrato modulo.js.
import { readdirSync, readFileSync, existsSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const SRC = new URL('../src/', import.meta.url).pathname
const archivos = (dir) => readdirSync(dir).flatMap((n) => {
  const p = join(dir, n)
  return statSync(p).isDirectory() ? archivos(p) : /\.(vue|js)$/.test(n) ? [p] : []
})
const imports = (archivo) => [...readFileSync(archivo, 'utf8').matchAll(/(?:import|from)\s*\(?\s*['"](@\/[^'"]+)['"]/g)].map((m) => m[1])

const errores = []
const modulos = readdirSync(join(SRC, 'modulos'))
for (const clave of modulos) {
  if (!existsSync(join(SRC, 'modulos', clave, 'modulo.js'))) errores.push(`src/modulos/${clave}/ necesita modulo.js`)
  for (const a of archivos(join(SRC, 'modulos', clave))) {
    for (const i of imports(a)) {
      const propio = i.startsWith(`@/modulos/${clave}/`)
      if (i.startsWith('@/modulos/') && !propio) errores.push(`${relative(SRC, a)} importa ${i} (otro módulo)`)
    }
  }
}
for (const carpeta of ['nucleo', 'componentes']) {
  for (const a of archivos(join(SRC, carpeta))) {
    for (const i of imports(a)) if (i.startsWith('@/modulos/')) errores.push(`${relative(SRC, a)} importa ${i}: lo común no conoce módulos`)
  }
}
if (errores.length) {
  console.error('Módulos no independientes:\n  ' + errores.join('\n  '))
  process.exit(1)
}
console.log(`Módulos independientes: ${modulos.join(', ')}`)
