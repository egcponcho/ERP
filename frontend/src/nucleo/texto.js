// Textos con datos: t('{0}–{1} de {2} registros', [1, 25, 300]) → «1–25 de 300 registros».
// Es el único punto por donde pasan los textos de los componentes comunes: si algún
// día la interfaz se traduce, aquí se busca la traducción sin tocar los componentes.
export function t(texto, args) {
  if (texto === null || texto === undefined) return texto
  const base = String(texto)
  return args ? base.replace(/\{(\d+)\}/g, (_, i) => args[i] ?? '') : base
}
