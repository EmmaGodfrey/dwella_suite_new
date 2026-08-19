<template>
  <TheBreadcrumbs main="Maps" title="Google Maps" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Map at a specified location</h5>
            <span>Display a map at a specified location and zoom level.</span>
          </div>
          <div class="card-body">
            <client-only> <GoogleMap :center="{ lat: 20.5937, lng: 78.9629 }" :zoom="12" style="width: auto; height: 500px"> </GoogleMap></client-only>
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
            <client-only>
              <GoogleMap
                :center="{ lat: 20.5937, lng: 78.9629 }"
                :zoom="6"
                style="width: auto; height: 500px"
                :options="{
                  region: 'VI',
                  language: 'vi',
                }"
              >
              </GoogleMap
            ></client-only>
          </div>
        </div>
      </div>
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Marker on the Map</h5>
            <span>Display a map highlighting points of interest</span>
          </div>
          <div class="card-body">
            <maps-markers-map />
          </div>
        </div>
      </div>
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Draggable Marker</h5>
            <span>Display a map highlighting points of interest</span>
          </div>
          <div class="card-body">
            <maps-draggable-marker />
          </div>
        </div>
      </div>
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h5>Polyline on the Map</h5>
            <span>Display a map with a line showing a known route</span>
          </div>
          <div class="card-body">
            <maps-google-polyline />
          </div>
        </div>
      </div>
      <div class="col-xl-6">
        <div class="card">
          <div class="card-header pb-0">
            <h4>Polygon on the Map</h4>
            <span>Display a map highlighting a region or area</span>
          </div>
          <div class="card-body">
            <maps-triangle-polygon />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Google Map | Cion - Premium Vue Admin Template',
});
</script>
