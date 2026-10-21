<script setup>
// Revisiones: versiones congeladas de la ficha con su vigencia, y qué cambió entre una y otra.
import { computed, onMounted, ref } from 'vue'
import { api } from '@/nucleo/api.js'
import { avisarError } from '@/nucleo/avisos.js'
import { fecha, valorTexto } from '@/nucleo/formato.js'
import EstadoVacio from '@/componentes/EstadoVacio.vue'
import Icono from '@/componentes/Icono.vue'
import Modal from '@/componentes/Modal.vue'

const props = defineProps({ producto: { type: Object, required: true } })
const emit = defineEmits(['publicar'])
const lista = ref(null)
const viendo = ref(null) // {revision, anterior}

onMounted(async () => {
  try { lista.value = (await api.get(`/productos/${props.producto.id}/revisiones`)).reverse() } catch (e) { avisarError(e); lista.value = [] }
})

async function ver(r) {
  try {
    const actual = await api.get(`/productos/${props.producto.id}/revisiones/${r.numero}`)
    const anterior = r.numero > 1 ? await api.get(`/productos/${props.producto.id}/revisiones/${r.numero - 1}`) : null
    viendo.value = { revision: actual, anterior }
  } catch (e) { avisarError(e) }
}

// Cambios en los datos generales y atributos respecto de la revisión anterior
const cambios = computed(() => {
  if (!viendo.value?.anterior) return null
  const a = viendo.value.anterior.datos
  const b = viendo.value.revision.datos
  const res = []
  for (const k of ['codigo', 'nombre', 'descripcion']) if (a[k] !== b[k]) res.push({ campo: k, antes: a[k], despues: b[k] })
  for (const k of new Set([...Object.keys(a.atributos), ...Object.keys(b.atributos)])) {
    if (JSON.stringify(a.atributos[k]) !== JSON.stringify(b.atributos[k])) res.push({ campo: k, antes: valorTexto(a.atributos[k]), despues: valorTexto(b.atributos[k]) })
  }
  if (a.variantes.length !== b.variantes.length) res.push({ campo: 'variantes', antes: a.variantes.length, despues: b.variantes.length })
  return res
})
</script>

<template>
  <section class="tarjeta">
    <header class="tarjeta-cabeza">
      <div><h2>Revisiones</h2><p>Cada revisión congela la ficha completa con su vigencia. No se pueden modificar.</p></div>
      <button class="btn primario" type="button" @click="emit('publicar')"><Icono nombre="publicar" :tam="16" />Publicar revisión</button>
    </header>
    <ol v-if="lista?.length" class="linea">
      <li v-for="r in lista" :key="r.numero" :class="{ vigente: !r.vigente_hasta }">
        <span class="punto" aria-hidden="true" />
        <div class="crece">
          <div class="fila"><strong>Revisión {{ r.numero }}</strong>
            <span v-if="!r.vigente_hasta" class="insignia ok">Vigente</span></div>
          <p class="tenue chico">{{ fecha(r.vigente_desde) }}<template v-if="r.vigente_hasta"> → {{ fecha(r.vigente_hasta) }}</template></p>
          <p v-if="r.motivo" class="motivo">{{ r.motivo }}</p>
        </div>
        <button class="btn chico" type="button" @click="ver(r)"><Icono nombre="ojo" :tam="14" />Ver</button>
      </li>
    </ol>
    <EstadoVacio v-else-if="lista" icono="historial" titulo="Sin revisiones publicadas"
                 texto="Publique una revisión cuando la ficha esté lista: queda una copia fija con fecha, útil para auditorías y cambios de receta.">
      <button class="btn primario" type="button" @click="emit('publicar')"><Icono nombre="publicar" :tam="16" />Publicar la primera</button>
    </EstadoVacio>
  </section>

  <Modal v-if="viendo" lateral ancho="600px" :titulo="`Revisión ${viendo.revision.numero}`"
         :descripcion="`${fecha(viendo.revision.vigente_desde)}${viendo.revision.motivo ? ' · ' + viendo.revision.motivo : ''}`" @cerrar="viendo = null">
    <div class="pila">
      <section v-if="cambios" class="pila-chica">
        <h3>Cambios respecto de la revisión {{ viendo.anterior.numero }}</h3>
        <table v-if="cambios.length" class="tabla">
          <thead><tr><th>Dato</th><th>Antes</th><th>Después</th></tr></thead>
          <tbody><tr v-for="c in cambios" :key="c.campo"><td><code>{{ c.campo }}</code></td><td class="antes">{{ c.antes ?? '—' }}</td><td class="despues">{{ c.despues ?? '—' }}</td></tr></tbody>
        </table>
        <p v-else class="tenue chico">Sin cambios en los datos generales ni en los atributos.</p>
      </section>
      <section class="pila-chica">
        <h3>Ficha congelada</h3>
        <dl class="datos">
          <div><dt>Código</dt><dd><code>{{ viendo.revision.datos.codigo }}</code></dd></div>
          <div><dt>Nombre</dt><dd>{{ viendo.revision.datos.nombre }}</dd></div>
          <div><dt>Tipo</dt><dd>{{ viendo.revision.datos.tipo.nombre }}</dd></div>
          <div><dt>Estado</dt><dd>{{ viendo.revision.datos.estado.nombre }}</dd></div>
          <div v-for="(v, k) in viendo.revision.datos.atributos" :key="k"><dt>{{ k }}</dt><dd>{{ valorTexto(v) }}</dd></div>
          <div><dt>Variantes</dt><dd>{{ viendo.revision.datos.variantes.length }}</dd></div>
          <div><dt>Presentaciones</dt><dd>{{ viendo.revision.datos.presentaciones.length }}</dd></div>
          <div><dt>Identificadores</dt><dd>{{ viendo.revision.datos.identificadores.length }}</dd></div>
        </dl>
      </section>
    </div>
  </Modal>
</template>

<style scoped>
.tarjeta { margin-top: var(--e-2); }
.linea { list-style: none; margin: 0; padding: var(--e-4) var(--e-5); position: relative; }
.linea li { display: flex; gap: var(--e-4); align-items: flex-start; padding-bottom: var(--e-5); position: relative; }
.linea li:not(:last-child)::before { content: ''; position: absolute; left: 5px; top: 16px; bottom: 0; width: 2px; background: var(--linea); }
.punto { width: 12px; height: 12px; border-radius: 50%; background: var(--borde-control); margin-top: 5px; flex: none; position: relative; }
.vigente .punto { background: var(--ok); box-shadow: 0 0 0 4px var(--ok-fondo); }
.motivo { margin-top: 4px; color: var(--tinta-2); }
.datos { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--e-3) var(--e-5); margin: 0; }
.datos dt { font-size: 12px; color: var(--tinta-3); font-weight: 550; }
.datos dd { margin: 0; }
.antes { color: var(--error); text-decoration: line-through; text-decoration-color: color-mix(in srgb, var(--error) 50%, transparent); }
.despues { color: var(--ok); font-weight: 550; }
</style>
