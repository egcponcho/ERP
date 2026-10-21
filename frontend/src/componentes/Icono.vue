<script setup>
// Íconos de trazo (24×24, trazo 1.8). Cada entrada es una lista de rutas SVG.
defineProps({ nombre: { type: String, required: true }, tam: { type: [Number, String], default: 18 } })

const ICONOS = {
  inicio: ['M3 11.5 12 4l9 7.5', 'M5.5 9.5V20h13V9.5', 'M10 20v-5.5h4V20'],
  caja: ['M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5z', 'M3.5 7.5 12 12l8.5-4.5', 'M12 12v9'],
  etiqueta: ['M3 12V4h8l10 10-8 8z', 'M7.5 8a.5.5 0 1 0 0-.01'],
  capas: ['m12 3 9 5-9 5-9-5z', 'm3 13 9 5 9-5'],
  regla: ['M3 17 17 3l4 4L7 21z', 'm7 13 2 2', 'm10 10 2 2', 'm13 7 2 2'],
  arbol: ['M5 4h5v5H5z', 'M14 15h5v5h-5z', 'M14 4h5v5h-5z', 'M7.5 9v8.5H14', 'M10 6.5h4'],
  bandera: ['M5 21V4', 'M5 4h11l-2 4 2 4H5'],
  codigo: ['M4 6v12', 'M7 6v12', 'M10.5 6v12', 'M13 6v12', 'M16.5 6v12', 'M20 6v12'],
  enlace: ['M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1', 'M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1'],
  historial: ['M3 12a9 9 0 1 0 3-6.7', 'M3 4v5h5', 'M12 8v4l3 2'],
  mas: ['M12 5v14', 'M5 12h14'],
  buscar: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z', 'm20 20-4-4'],
  cerrar: ['M6 6l12 12', 'M18 6 6 18'],
  editar: ['M4 20h4L19 9l-4-4L4 16z', 'm13.5 6.5 4 4'],
  borrar: ['M4 7h16', 'M10 11v6', 'M14 11v6', 'M6 7l1 13h10l1-13', 'M9 7V4h6v3'],
  check: ['m5 12.5 4.5 4.5L19 7.5'],
  alerta: ['M12 3 2 20h20z', 'M12 10v4', 'M12 17h.01'],
  info: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 11v5', 'M12 8h.01'],
  derecha: ['m9 6 6 6-6 6'],
  izquierda: ['m15 6-6 6 6 6'],
  abajo: ['m6 9 6 6 6-6'],
  sol: ['M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M12 2v2', 'M12 20v2', 'm4.9 4.9 1.4 1.4', 'm17.7 17.7 1.4 1.4', 'M2 12h2', 'M20 12h2', 'm4.9 19.1 1.4-1.4', 'm17.7 6.3 1.4-1.4'],
  luna: ['M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z'],
  monitor: ['M3 5h18v11H3z', 'M8 20h8', 'M12 16v4'],
  ajustes: ['M4 6h10', 'M18 6h2', 'M4 12h4', 'M12 12h8', 'M4 18h12', 'M20 18h0', 'M16 4v4', 'M10 10v4', 'M18 16v4'],
  cuadricula: ['M4 4h7v7H4z', 'M13 4h7v7h-7z', 'M4 13h7v7H4z', 'M13 13h7v7h-7z'],
  publicar: ['M12 15V4', 'm7 9 5-5 5 5', 'M5 20h14'],
  flecha: ['M5 12h14', 'm13 6 6 6-6 6'],
  heredado: ['M6 4v9a4 4 0 0 0 4 4h8', 'm14 13 4 4-4 4'],
  ojo: ['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
  ojoNo: ['M3 3l18 18', 'M10.6 5.1A10.5 10.5 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2', 'M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6', 'M9.9 9.9a3 3 0 0 0 4.2 4.2'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  estrella: ['m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z'],
}
</script>

<template>
  <svg :width="tam" :height="tam" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false" class="icono">
    <path v-for="(d, i) in ICONOS[nombre] || []" :key="i" :d="d" />
  </svg>
</template>

<style scoped>
.icono { flex: none; display: block; }
</style>
