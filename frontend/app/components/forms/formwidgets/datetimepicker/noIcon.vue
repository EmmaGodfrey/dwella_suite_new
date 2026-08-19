<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">No Icon (input field only)</label>
    <div class="col-xl-5 col-sm-7 col-lg-8">
      <client-only> <Datepicker v-model="date1" :flow="flow" class="digits" id="dt-noicon" type="text" data-toggle="datetimepicker" data-target="#dt-noicon" /></client-only>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date1 = ref();
const flow = ref<string[]>(['calendar', 'time']);
</script>
