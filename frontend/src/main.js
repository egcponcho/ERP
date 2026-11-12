// Punto de entrada: estilos, rutas y directivas globales.
import { createApp } from 'vue'
// Inter: la letra más cercana a la del sistema de Apple para quien no usa un equipo Apple
import '@fontsource-variable/inter'
import './estilos/index.css'
import App from './App.vue'
import router from './router.js'
import { vFiltros, vFlotante, vTarjetas } from './nucleo/directivas.js'

createApp(App).use(router).directive('filtros', vFiltros).directive('flotante', vFlotante).directive('tarjetas', vTarjetas).mount('#app')
