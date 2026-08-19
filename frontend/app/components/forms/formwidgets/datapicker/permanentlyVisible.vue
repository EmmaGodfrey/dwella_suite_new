<template>
  <div class="form-group row mb-0">
    <label class="col-sm-3 col-form-label text-end">Permanently visible Datepicker</label>
    <div class="col-sm-3">
      <client-only> <Datepicker :inline="{ input: false }" text-input auto-apply /></client-only>
    </div>
  </div>
</template>
<script setup>
const date = ref();
</script>
