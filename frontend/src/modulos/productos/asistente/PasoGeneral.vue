<script setup>
// Paso 2: lo que tiene cualquier producto. El código se genera solo si el tipo tiene numeración.
import { computed } from 'vue'
import { heredado } from '@/nucleo/esquemaLocal.js'
import { b } from './borrador.js'

const props = defineProps({ esquema: { type: Object, required: true },
                            datos: { type: Object, required: true }, errores: { type: Array, default: () => [] } })
const msj = (c) => props.errores.filter((e) => e.campo === `producto.${c}`).map((e) => e.mensaje).join(' ')
const tipo = computed(() => props.datos.tipos.find((t) => t.id === b.tipoId))
const numeracion = computed(() => (tipo.value ? heredado(tipo.value, props.datos.tipos, 'plantilla_codigo') : null))
const sueltos = computed(() => props.errores.filter((e) => !['producto.nombre', 'producto.codigo', 'producto.unidad_id', 'producto.descripcion'].includes(e.campo)))
</script>

<template>
  <section class="panel">
    <div class="panel-cabeza"><div><h2>Datos generales</h2><p>El nombre con que se reconoce el producto y la unidad en que se cuenta o se mide.</p></div></div>
    <div v-if="sueltos.length" class="nota error mb-3" role="alert"><ul class="lista-mensajes"><li v-for="(e, i) in sueltos" :key="i">{{ e.mensaje }}</li></ul></div>
    <div class="rejilla-campos">
      <label class="campo col-completa" :class="{ 'con-error': msj('nombre') }"><span class="req">Nombre</span>
        <input v-model="b.producto.nombre" class="entrada" maxlength="200" placeholder="Ej.: Bota de trabajo dieléctrica" autofocus />
        <small v-if="msj('nombre')" class="campo-error">{{ msj('nombre') }}</small></label>
      <label class="campo" :class="{ 'con-error': msj('codigo') }"><span :class="{ req: !numeracion }">Código</span>
        <input v-model="b.producto.codigo" class="entrada mono" maxlength="60" :placeholder="numeracion ? 'Automático' : 'Ej.: BOT-001'" />
        <small v-if="msj('codigo')" class="campo-error">{{ msj('codigo') }}</small>
        <small v-else class="ayuda">{{ numeracion ? `Si lo deja vacío se numera con ${numeracion}.` : 'Este tipo no numera solo: escriba el código.' }}</small></label>
      <label class="campo" :class="{ 'con-error': msj('unidad_id') }"><span class="req">Unidad base</span>
        <select v-model="b.producto.unidad_id" class="entrada">
          <option :value="null" disabled>Elegir…</option>
          <option v-for="u in datos.unidades.filter((x) => x.activa)" :key="u.id" :value="u.id">{{ u.nombre }} ({{ u.codigo }})</option>
        </select>
        <small v-if="msj('unidad_id')" class="campo-error">{{ msj('unidad_id') }}</small>
        <small v-else class="ayuda">En la que se cuentan las existencias y las presentaciones.</small></label>
      <label class="campo col-completa"><span>Descripción</span>
        <textarea v-model="b.producto.descripcion" class="entrada" rows="3" placeholder="Opcional: para catálogos y documentos" /></label>
    </div>
  </section>
</template>
