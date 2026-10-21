<script setup>
defineProps({ filas: { type: Number, default: 5 }, columnas: { type: Number, default: 4 } })
</script>

<template>
  <tr v-for="f in filas" :key="f" aria-hidden="true">
    <td v-for="c in columnas" :key="c"><span class="esqueleto" :style="{ width: `${40 + ((f * 7 + c * 13) % 50)}%` }" /></td>
  </tr>
</template>
