// Esquema de un tipo armado en el navegador con la lista de tipos y atributos
// (para mostrar tarjetas sin pedir el esquema de cada tipo al servidor). La
// fuente de verdad sigue siendo /tipos-producto/{id}/esquema.
export function rutaTipo(tipo, tipos) {
  const r = []
  let x = tipo
  while (x && !r.includes(x)) { r.unshift(x); x = tipos.find((t) => t.id === x.padre_id) }
  return r
}

export function camposDe(tipo, tipos, atributos) {
  const porAtributo = new Map()
  for (const t of rutaTipo(tipo, tipos)) for (const a of t.asignaciones || []) porAtributo.set(a.atributo_id, a)
  return [...porAtributo.values()].filter((a) => !a.oculto)
    .map((a) => ({ ...a, atributo: atributos.find((x) => x.id === a.atributo_id) })).filter((a) => a.atributo?.activo)
}

export function heredado(tipo, tipos, campo) {
  return rutaTipo(tipo, tipos).reverse().map((t) => t[campo]).find((v) => v !== null && v !== undefined && v !== '') ?? null
}
