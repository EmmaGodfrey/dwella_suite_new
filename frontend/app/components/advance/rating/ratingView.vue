<template>
  <div class="col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Clickable Value</h5>
      </div>
      <div class="card-body">
        <div class="rating-container digits">
          <ClientOnly>
            <star-rating :show-rating="false" :star-size="20" :max-rating="10" @update:rating="rating = $event"></star-rating>
          </ClientOnly>
          <pre class="mb-0 rating-pre px-2">Rating {{ rating }}</pre>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Star Rating</h5>
      </div>
      <div class="card-body">
        <div class="rating-container digits">
          <ClientOnly>
            <star-rating :star-size="20" :max-rating="10" :increment="0.01"></star-rating>
          </ClientOnly>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const rating = ref<string>('0');
</script>
