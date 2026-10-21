<script setup>
// Paso 1: qué se da de alta. Se elige un tipo (cada tarjeta dice qué
// características pide y si maneja variantes) o se crea uno nuevo aquí mismo.
import { computed, ref } from 'vue'
import { buscador } from '@/nucleo/busqueda.js'
import { camposDe, rutaTipo } from '@/nucleo/esquemaLocal.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import CreadorTipo from './CreadorTipo.vue'
import { b } from './borrador.js'

const props = defineProps({ datos: { type: Object, required: true } })
const emit = defineEmits(['elegir', 'creado'])
const busqueda = ref('')
const creando = ref(false)

const tarjetas = computed(() => {
  const coincide = buscador(busqueda.value)
  return props.datos.tipos.filter((t) => t.activo).map((t) => {
    const campos = camposDe(t, props.datos.tipos, props.datos.atributos)
    const ruta = rutaTipo(t, props.datos.tipos).map((x) => x.nombre)
    return { tipo: t, ruta, campos: campos.filter((c) => c.nivel === 'producto'), ejes: campos.filter((c) => c.es_eje) }
  }).filter((x) => coincide([...x.ruta, x.tipo.codigo, ...x.campos.map((c) => c.atributo.nombre)]))
    .sort((a, b) => a.ruta.join(' ').localeCompare(b.ruta.join(' ')))
})
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza">
      <div><h2>¿Qué tipo de producto va a dar de alta?</h2>
        <p>El tipo define qué datos se piden, cuáles distinguen variantes y cómo se numera. Elija uno o cree uno nuevo.</p></div>
      <button v-if="!creando" type="button" class="btn" @click="creando = true"><Icono nombre="mas" :tam="15" />Crear tipo nuevo</button>
    </div>

    <CreadorTipo v-if="creando" :datos="datos" @cerrar="creando = false" @creado="(t) => { creando = false; emit('creado', t) }" />

    <template v-if="datos.listos && datos.tipos.some((t) => t.activo)">
      <label class="buscador mb-3">
        <Icono nombre="buscar" :tam="16" />
        <input v-model="busqueda" class="entrada" type="search" placeholder="Buscar tipo o característica" aria-label="Buscar tipo de producto" />
      </label>
      <div class="tarjetas-eleccion" role="list">
        <button v-for="x in tarjetas" :key="x.tipo.id" type="button" role="listitem" class="tarjeta-eleccion" :aria-pressed="b.tipoId === x.tipo.id"
                @click="emit('elegir', x.tipo)">
          <small v-if="x.ruta.length > 1">{{ x.ruta.slice(0, -1).join(' › ') }}</small>
          <b>{{ x.tipo.nombre }}</b>
          <small>{{ x.campos.length ? x.campos.map((c) => c.atributo.nombre).slice(0, 4).join(', ') + (x.campos.length > 4 ? '…' : '') : 'Sin características propias' }}</small>
          <span class="insignias">
            <span v-if="x.ejes.length" class="etiqueta acento ms-0">Variantes por {{ x.ejes.map((c) => c.atributo.nombre.toLowerCase()).join(' y ') }}</span>
            <span v-else class="etiqueta ms-0">Sin variantes</span>
          </span>
        </button>
      </div>
      <p v-if="!tarjetas.length" class="ayuda">Ningún tipo coincide con «{{ busqueda }}». <button type="button" class="btn-texto" @click="creando = true">Crear uno nuevo</button></p>
    </template>
    <EstadoVacio v-else-if="datos.listos && !creando" icono="capas" titulo="Aún no hay tipos de producto"
                 texto="Cree el primero aquí mismo: le pone nombre y elige sus características (color, talla, peso, pureza…).">
      <button type="button" class="btn btn-primario" @click="creando = true"><Icono nombre="mas" :tam="16" />Crear tipo de producto</button>
    </EstadoVacio>
    <div v-else-if="!datos.listos" class="tarjetas-eleccion" aria-busy="true">
      <span v-for="i in 3" :key="i" class="esqueleto" style="height: 96px" />
    </div>
  </section>
</template>
