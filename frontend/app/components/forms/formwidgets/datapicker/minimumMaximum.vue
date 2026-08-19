<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">Minimum and maximum dates</label>
    <div class="col-xl-5 col-sm-9">
      <client-only> <datepicker class="digits" v-model="date" :format="format" /></client-only>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date = ref<Date | null>(null);

const format = (date: Date | null): string => {
  if (date === null) {
    return '';
  }

  const day = date.getDate();
  const month = date.getMonth() + 1;
  const year = date.getFullYear();

  return ` ${day}/${month}/${year}`;
};
</script>
