<script setup>
// Paso: variantes. Se eligen los valores de cada eje (talla, color…) y se crean
// todas las combinaciones; en la vista previa se puede quitar las que no van.
import { computed, reactive } from 'vue'
import { b, claveCombinacion } from './borrador.js'
import CampoAtributo from '@/componentes/CampoAtributo.vue'
import Icono from '@/componentes/Icono.vue'
import TablaDatos from '@/componentes/TablaDatos.vue'

const props = defineProps({ esquema: { type: Object, required: true }, datos: { type: Object, required: true },
                            combos: { type: Array, required: true }, errores: { type: Array, default: () => [] } })
const ejes = computed(() => props.esquema.campos.filter((c) => c.es_eje))
const otros = computed(() => props.esquema.campos.filter((c) => c.nivel === 'variante' && !c.es_eje))
const nuevo = reactive({})

// Cada eje empieza con su lista vacía (antes de dibujar: no se escribe el borrador durante el dibujo)
for (const e of ejes.value) if (!Array.isArray(b.ejes[e.atributo.codigo])) b.ejes[e.atributo.codigo] = []
const valores = (e) => b.ejes[e.atributo.codigo] || []
function alternar(e, v) {
  const l = valores(e)
  const i = l.indexOf(v)
  if (i >= 0) l.splice(i, 1)
  else l.push(v)
}
function todas(e) {
  const activas = e.atributo.opciones.filter((o) => o.activa).map((o) => o.codigo)
  b.ejes[e.atributo.codigo] = valores(e).length === activas.length ? [] : activas
}
function agregar(e) {
  const t = (nuevo[e.atributo.codigo] || '').trim()
  if (!t) return
  for (const parte of t.split(',').map((x) => x.trim()).filter(Boolean)) {
    const v = ['entero', 'decimal'].includes(e.atributo.tipo_dato) ? Number(parte) : parte
    if (!valores(e).includes(v)) valores(e).push(v)
  }
  nuevo[e.atributo.codigo] = ''
}

const nombre = (e, v) => e.atributo.opciones?.find((o) => o.codigo === v)?.nombre ?? (v === true ? 'Sí' : v === false ? 'No' : String(v))
const ficha = (e, v) => (e.atributo.opciones?.find((o) => o.codigo === v)?.codigo ?? String(v)).toString().toUpperCase().replace(/[^A-Z0-9.]+/g, '')
const prefijo = computed(() => b.producto.codigo || 'CÓDIGO')
function sku(c) {
  const fichas = Object.fromEntries(ejes.value.map((e) => [e.atributo.codigo, ficha(e, c[e.atributo.codigo])]))
  if (!props.esquema.plantilla_sku) return [prefijo.value, ...Object.values(fichas)].join('-')
  return props.esquema.plantilla_sku.replace(/\{(\w+)\}/g, (_, k) => (k === 'producto' ? prefijo.value : fichas[k] ?? `{${k}}`))
}

// Cada fila lleva el nombre de cada valor (n_<eje>) para mostrarlo, ordenarlo y filtrarlo
const filas = computed(() => props.combos.map((c) => ({
  _clave: claveCombinacion(c), _sku: sku(c), ...Object.fromEntries(ejes.value.map((e) => [`n_${e.atributo.codigo}`, nombre(e, c[e.atributo.codigo])])) })))
const columnas = computed(() => [
  ...ejes.value.map((e) => ({ clave: `n_${e.atributo.codigo}`, texto: e.atributo.nombre })),
  { clave: '_sku', texto: 'SKU (vista previa)', filtro: false },
])
const seleccion = computed({
  get: () => filas.value.filter((f) => !b.excluidas.includes(f._clave)).map((f) => f._clave),
  set: (claves) => { b.excluidas = filas.value.map((f) => f._clave).filter((k) => !claves.includes(k)) },
})
const msjVariante = computed(() => props.errores.map((e) => {
  const i = Number(e.campo.split('.')[1])
  const incluidas = filas.value.filter((f) => !b.excluidas.includes(f._clave))
  const f = incluidas[i]
  return f ? `${ejes.value.map((x) => f[`n_${x.atributo.codigo}`]).join(" / ")}: ${e.mensaje}` : e.mensaje
}))
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>Variantes</h2>
        <p>Elija los valores de {{ ejes.map((e) => e.atributo.nombre.toLowerCase()).join(' y ') }}. Se crea una variante (SKU) por cada combinación.</p></div>
      <span class="etiqueta" :class="seleccion.length ? 'acento' : ''">{{ seleccion.length }} variantes</span>
    </div>
    <div v-if="msjVariante.length" class="nota error mb-3" role="alert"><ul class="lista-mensajes"><li v-for="(m, i) in msjVariante" :key="i">{{ m }}</li></ul></div>

    <div v-for="e in ejes" :key="e.atributo.id" class="eje">
      <div class="fila-flex entre">
        <h3>{{ e.atributo.nombre }} <span class="ayuda">· {{ valores(e).length }} elegidos</span></h3>
        <button v-if="e.atributo.tipo_dato === 'opcion'" type="button" class="btn btn-chico btn-fantasma" @click="todas(e)">
          {{ valores(e).length === e.atributo.opciones.filter((o) => o.activa).length ? 'Quitar todos' : 'Elegir todos' }}</button>
      </div>
      <div v-if="e.atributo.tipo_dato === 'opcion'" class="opciones-chips" role="group" :aria-label="e.atributo.nombre">
        <button v-for="o in e.atributo.opciones.filter((x) => x.activa)" :key="o.codigo" type="button" class="opcion-chip"
                :aria-pressed="valores(e).includes(o.codigo)" @click="alternar(e, o.codigo)">
          <Icono v-if="valores(e).includes(o.codigo)" nombre="check" :tam="13" />{{ o.nombre }}</button>
      </div>
      <div v-else-if="e.atributo.tipo_dato === 'booleano'" class="opciones-chips">
        <button v-for="v in [true, false]" :key="String(v)" type="button" class="opcion-chip" :aria-pressed="valores(e).includes(v)" @click="alternar(e, v)">{{ v ? 'Sí' : 'No' }}</button>
      </div>
      <template v-else>
        <div class="fila-flex">
          <input v-model="nuevo[e.atributo.codigo]" class="entrada crece" :aria-label="`Valores de ${e.atributo.nombre}`"
                 :placeholder="`Escriba valores separados por coma${e.atributo.unidad_defecto ? ` (en ${e.atributo.unidad_defecto})` : ''} y presione Enter`" @keydown.enter.prevent="agregar(e)" />
          <button type="button" class="btn" @click="agregar(e)">Agregar</button>
        </div>
        <div v-if="valores(e).length" class="chips mt-chico">
          <span v-for="v in valores(e)" :key="String(v)" class="chip">{{ v }}
            <button type="button" :aria-label="`Quitar ${v}`" @click="alternar(e, v)"><Icono nombre="cerrar" :tam="12" /></button></span>
        </div>
      </template>
    </div>

    <div v-if="otros.length" class="eje">
      <h3>Datos iguales para todas las variantes</h3>
      <p class="ayuda mb-2">Después puede cambiarlos en cada variante desde la ficha.</p>
      <div class="rejilla-campos">
        <CampoAtributo v-for="c in otros" :key="c.atributo.id" v-model="b.comunes[c.atributo.codigo]" :campo="c" :unidades="datos.unidades" id-base="comun" />
      </div>
    </div>
  </section>

  <section v-if="filas.length" class="panel">
    <div class="panel-cabeza">
      <div><h2>Vista previa</h2><p>Desmarque las combinaciones que no existen. Los SKU definitivos se ven en el último paso.</p></div>
    </div>
    <TablaDatos tabla="asistente-variantes" :columnas="columnas" :filas="filas" clave-fila="_clave" seleccionable v-model:seleccion="seleccion"
                :vistas-guardadas="false" etiqueta="Combinaciones">
      <template #celda-_sku="{ fila }"><code :class="{ apagado: b.excluidas.includes(fila._clave) }">{{ fila._sku }}</code></template>
    </TablaDatos>
  </section>
</template>

<style scoped>
.eje { display: flex; flex-direction: column; gap: 10px; padding: 14px 0; border-top: 1px solid var(--linea-suave); }
.eje:first-of-type { border-top: 0; padding-top: 0; }
</style>
