// Formatos de presentación comunes a todos los módulos.

// Fecha y hora en el idioma del navegador: «12 nov 2026, 10:30»
export function fecha(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es', { dateStyle: 'medium', timeStyle: 'short' })
}

// Número con separador de miles, sin decimales de más
export const numero = (n) => (n === null || n === undefined ? '—' : Number(n).toLocaleString('es'))
