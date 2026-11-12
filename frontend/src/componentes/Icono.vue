<script setup>
// Íconos de trazo (24×24), de líneas redondeadas como SF Symbols. Cada entrada es la
// lista de trazos SVG. Solo están los que la aplicación usa: agregue aquí los nuevos.
const props = defineProps({ nombre: { type: String, required: true }, tam: { type: [Number, String], default: 18 } })

const ICONOS = {
  texto: ['M5 6V4h14v2', 'M12 4v16', 'M9 20h6'],
  campo: ['M8 4H7a2 2 0 0 0-2 2v4l-2 2 2 2v4a2 2 0 0 0 2 2h1', 'M16 4h1a2 2 0 0 1 2 2v4l2 2-2 2v4a2 2 0 0 1-2 2h-1'],
  barras: ['M4 5v14', 'M7 5v14', 'M10.5 5v14', 'M12.5 5v14', 'M16 5v14', 'M18 5v14', 'M20 5v14'],
  linea: ['M4 18 20 6'],
  tabla: ['M4 4h16v16H4z', 'M4 9h16', 'M4 14h16', 'M10 9v11'],
  cuadricula: ['M4 4h16v16H4z', 'M4 9.3h16', 'M4 14.7h16', 'M9.3 4v16', 'M14.7 4v16'],
  inicio: ['M3 11.5 12 4l9 7.5', 'M5.5 9.5V20h13V9.5', 'M10 20v-5.5h4V20'],
  caja: ['M3.5 7.5 12 3l8.5 4.5v9L12 21l-8.5-4.5z', 'M3.5 7.5 12 12l8.5-4.5', 'M12 12v9', 'M7.8 5.2l8.4 4.6'],
  capas: ['M12 3 3 8l9 5 9-5z', 'm3 13 9 5 9-5', 'm3 16.5 9 5 9-5'],
  salir: ['M9 4H5v16h4', 'M16 8l4 4-4 4', 'M20 12H9'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  cerrar: ['M6 6l12 12', 'M18 6 6 18'],
  check: ['m5 12.5 4.5 4.5L19 7.5'],
  alerta: ['M12 3.5 2.5 20h19z', 'M12 10v4.5', 'M12 17.2v.3'],
  info: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M12 11v5.5', 'M12 7.8v.3'],
  flecha: ['M5 12h14', 'm13 6 6 6-6 6'],
  atras: ['M19 12H5', 'm11 6-6 6 6 6'],
  // Chevron de «atrás» de la barra de navegación de iOS
  'atras-ios': ['m15 4.5-7.5 7.5 7.5 7.5'],
  derecha: ['m9 6 6 6-6 6'],
  abajo: ['m6 9 6 6 6-6'],
  arriba: ['m6 15 6-6 6 6'],
  arribaabajo: ['m8 9 4-4 4 4', 'm8 15 4 4 4-4'],
  filtro: ['M4 5h16l-6 7.5V19l-4 1.5v-8z'],
  columnas: ['M4 4h16v16H4z', 'M9.5 4v16', 'M14.5 4v16'],
  buscar: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z', 'm20 20-4-4'],
  mas: ['M12 5v14', 'M5 12h14'],
  ojo: ['M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
  editar: ['M4 20h4L19 9l-4-4L4 16z', 'M13.5 6.5l4 4'],
  basura: ['M4 7h16', 'M9 7V4h6v3', 'M6 7l1 13h10l1-13'],
  lista: ['M9 6h11', 'M9 12h11', 'M9 18h11', 'M4.5 6h.5', 'M4.5 12h.5', 'M4.5 18h.5'],
  historial: ['M3.5 12a8.5 8.5 0 1 0 2.5-6', 'M3 4v4h4', 'M12 8v4.5l3 1.5'],
  etiqueta: ['M3.5 12.2V4.5a1 1 0 0 1 1-1h7.7l8.3 8.3a1 1 0 0 1 0 1.4l-7.3 7.3a1 1 0 0 1-1.4 0z', 'M8 8.2a.4.4 0 1 0 0-.01'],
  sol: ['M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M12 2.5v2', 'M12 19.5v2', 'M2.5 12h2', 'M19.5 12h2', 'm5.3 5.3 1.4 1.4', 'm17.3 17.3 1.4 1.4', 'm5.3 18.7 1.4-1.4', 'm17.3 6.7 1.4-1.4'],
  luna: ['M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z'],
  monitor: ['M3 4.5h18v12H3z', 'M8.5 20.5h7', 'M12 16.5v4'],
  escala: ['M12 4v16', 'M7 20h10', 'M5 8h14', 'M5 8l-2.5 6a2.5 2.5 0 0 0 5 0z', 'M19 8l-2.5 6a2.5 2.5 0 0 0 5 0z'],
  regla: ['M3 17 17 3l4 4L7 21z', 'm7 13 2 2', 'm10 10 2 2', 'm13 7 2 2'],
  arbol: ['M5 4h5v5H5z', 'M14 15h5v5h-5z', 'M14 4h5v5h-5z', 'M7.5 9v8.5H14', 'M10 6.5h4'],
  bandera: ['M5 21V4', 'M5 4h11l-2 4 2 4H5'],
  codigo: ['M4 6v12', 'M7 6v12', 'M10.5 6v12', 'M13 6v12', 'M16.5 6v12', 'M20 6v12'],
  enlace: ['M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1', 'M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1'],
  publicar: ['M12 15V4', 'm7 9 5-5 5 5', 'M5 20h14'],
  heredado: ['M6 4v9a4 4 0 0 0 4 4h8', 'm14 13 4 4-4 4'],
  'ojo-no': ['M3 3l18 18', 'M10.6 5.1A10.5 10.5 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2', 'M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6', 'M9.9 9.9a3 3 0 0 0 4.2 4.2'],
}
</script>

<template>
  <svg :width="props.tam" :height="props.tam" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
    <path v-for="(d, i) in ICONOS[props.nombre] || []" :key="i" :d="d" />
  </svg>
</template>
