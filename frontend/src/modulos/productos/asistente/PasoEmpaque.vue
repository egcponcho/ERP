<script setup>
// Paso: cómo se empaca o vende (presentaciones) y sus códigos de barras u otros
// códigos. Se capturan en filas, como líneas de un documento; todo es opcional.
import { computed } from 'vue'
import Icono from '@/componentes/Icono.vue'
import { b } from './borrador.js'

const props = defineProps({ datos: { type: Object, required: true }, errores: { type: Array, default: () => [] } })
const unidad = computed(() => props.datos.unidades.find((u) => u.id === b.producto.unidad_id))
const msjs = (seccion, i) => props.errores.filter((e) => e.campo === `${seccion}.${i}` || e.campo.startsWith(`${seccion}.${i}.`)).map((e) => e.mensaje)
const unidadUN = () => props.datos.unidades.find((u) => u.codigo === 'UN')?.id ?? props.datos.unidades[0]?.id ?? null

function agregarPresentacion() {
  b.presentaciones.push({ nombre: '', codigo: '', cantidad: '', unidad_id: unidadUN() })
}
function agregarCodigo() {
  b.identificadores.push({ tipo_id: props.datos.tiposIdentificador[0]?.id ?? null, valor: '', presentacion_codigo: '' })
}
function codigoDesdeNombre(x) {
  if (x._tocado) return
  const m = x.nombre.match(/(\d+)/)
  const letras = x.nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3)
  x.codigo = `${letras}${m ? m[1] : ''}`.slice(0, 40)
}
const patron = (id) => props.datos.tiposIdentificador.find((t) => t.id === id)?.patron
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>Presentaciones</h2><p>Cómo se empaca o se vende: caja de 12, bulto de 50 kg, tambor de 200 L… Opcional.</p></div>
      <button type="button" class="btn btn-chico" @click="agregarPresentacion"><Icono nombre="mas" :tam="14" />Agregar presentación</button>
    </div>
    <div v-if="b.presentaciones.length" class="lineas">
      <div v-for="(x, i) in b.presentaciones" :key="i" class="linea" :class="{ invalida: msjs('presentaciones', i).length }">
        <span class="linea-num">{{ i + 1 }}</span>
        <label class="campo"><span class="req">Nombre</span><input v-model="x.nombre" class="entrada" placeholder="Caja de 12" @input="codigoDesdeNombre(x)" /></label>
        <label class="campo"><span class="req">Código</span><input v-model="x.codigo" class="entrada mono" maxlength="40" placeholder="CAJ12" @input="x._tocado = true" /></label>
        <label class="campo"><span class="req">Contiene</span>
          <span class="con-unidad"><input v-model="x.cantidad" class="entrada num" type="number" min="0" step="any" /><small>{{ unidad?.codigo }}</small></span></label>
        <label class="campo"><span>Se cuenta en</span>
          <select v-model="x.unidad_id" class="entrada"><option v-for="u in datos.unidades" :key="u.id" :value="u.id">{{ u.nombre }}</option></select></label>
        <button type="button" class="btn-icono quitar" :aria-label="`Quitar presentación ${i + 1}`" @click="b.presentaciones.splice(i, 1)"><Icono nombre="basura" :tam="16" /></button>
        <ul v-if="msjs('presentaciones', i).length" class="lista-mensajes error-linea"><li v-for="(m, j) in msjs('presentaciones', i)" :key="j">{{ m }}</li></ul>
      </div>
    </div>
    <p v-else class="ayuda">Sin presentaciones. El producto se maneja solo en su unidad base ({{ unidad?.nombre?.toLowerCase() || '—' }}).</p>
  </section>

  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>Códigos de barras y otros códigos</h2><p>EAN, UPC, código del proveedor… del producto o de una de sus presentaciones. Opcional.</p></div>
      <button type="button" class="btn btn-chico" :disabled="!datos.tiposIdentificador.length" @click="agregarCodigo"><Icono nombre="mas" :tam="14" />Agregar código</button>
    </div>
    <div v-if="b.identificadores.length" class="lineas">
      <div v-for="(x, i) in b.identificadores" :key="i" class="linea" :class="{ invalida: msjs('identificadores', i).length }">
        <span class="linea-num">{{ i + 1 }}</span>
        <label class="campo"><span class="req">Tipo</span>
          <select v-model="x.tipo_id" class="entrada"><option v-for="t in datos.tiposIdentificador" :key="t.id" :value="t.id">{{ t.nombre }}</option></select></label>
        <label class="campo"><span class="req">Código</span><input v-model="x.valor" class="entrada mono" maxlength="100" :placeholder="patron(x.tipo_id) ? `Formato ${patron(x.tipo_id)}` : ''" /></label>
        <label class="campo"><span>Es de</span>
          <select v-model="x.presentacion_codigo" class="entrada">
            <option value="">El producto</option>
            <option v-for="p in b.presentaciones.filter((p) => p.codigo)" :key="p.codigo" :value="p.codigo">{{ p.nombre || p.codigo }}</option>
          </select></label>
        <button type="button" class="btn-icono quitar" :aria-label="`Quitar código ${i + 1}`" @click="b.identificadores.splice(i, 1)"><Icono nombre="basura" :tam="16" /></button>
        <ul v-if="msjs('identificadores', i).length" class="lista-mensajes error-linea"><li v-for="(m, j) in msjs('identificadores', i)" :key="j">{{ m }}</li></ul>
      </div>
    </div>
    <p v-else class="ayuda">{{ datos.tiposIdentificador.length ? 'Sin códigos adicionales. También puede agregarlos después desde la ficha.' : 'No hay tipos de código configurados.' }}</p>
  </section>
</template>

<style scoped>
.lineas { display: flex; flex-direction: column; gap: 10px; }
.linea { display: grid; grid-template-columns: 28px repeat(auto-fit, minmax(150px, 1fr)) auto; gap: 10px; align-items: end; padding: 10px; border: 1px solid var(--linea); border-radius: 10px; }
.linea.invalida { border-color: var(--error); }
.linea-num { align-self: center; color: var(--tinta-3); font-weight: 650; font-size: 0.85rem; }
.quitar { align-self: center; }
.error-linea { grid-column: 1 / -1; color: var(--error); margin: 0; font-size: 0.84rem; }
.con-unidad { display: flex; align-items: center; gap: 6px; }
.con-unidad .entrada { flex: 1; min-width: 0; }
.con-unidad small { color: var(--tinta-2); }
@media (max-width: 720px) { .linea { grid-template-columns: 1fr 1fr; } .linea-num { display: none; } }
</style>
