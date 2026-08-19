<template>
  <client-only>
    <l-map :zoom="simple.zoom" global-leaflet="false" :center="simple.center" :useGlobalLeaflet="false" style="height: 500px">
      <l-tile-layer :url="simple.url"></l-tile-layer>
    </l-map>
  </client-only>
</template>
<script lang="ts" setup>
const simple = {
  zoom: 5,
  center: [49.439557, 234.558105],
  url: 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
};
</script>
