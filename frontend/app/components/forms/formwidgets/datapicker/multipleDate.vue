<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">Selecting multiple dates</label>
    <div class="col-xl-5 col-sm-9">
      <client-only>
        <datepicker class="datepicker-here digits" v-model="date" multiDates />
      </client-only>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date = ref();
</script>
