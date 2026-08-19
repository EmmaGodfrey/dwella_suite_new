<template>
  <client-only>
    <GoogleMap :center="center" :zoom="12" style="width: 100%; height: 500px">
      <Marker v-for="(location, index) in positions.lists" :key="index" :options="{ position: { lat: location.lat, lng: location.lng } }" /> </GoogleMap
  ></client-only>
</template>
<script lang="ts" setup>
interface cent {
  lat: number;
  lng: number;
}
const center = ref<cent>({ lat: 42.35805, lng: -71.0636 });
const positions = ref({
  lists: ref<cent[]>([{ lat: 42.35805, lng: -71.0636 }]),
});
</script>
