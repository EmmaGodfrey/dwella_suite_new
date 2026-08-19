<template>
  <TheBreadcrumbs main="Maps" title="Vue Leaflet" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Simple Map</h5>
          </div>
          <div class="card-body">
            <maps-simple-map />
          </div>
        </div>
      </div>
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Multi-language support</h5>
            <span>Display a map with labels in a foreign language</span>
          </div>
          <div class="card-body">
            <maps-multi-language />
          </div>
        </div>
      </div>
      <div class="col-xl-12">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Multi-language support</h5>
            <span>Display a map with labels in a foreign language</span>
          </div>
          <div class="card-body">
            <maps-multi-language2 />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Leaflet Map | Cion - Premium Vue Admin Template',
});
</script>
