<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">Date Only</label>
    <div class="col-xl-5 col-sm-7 col-lg-8">
      <div class="input-group date" id="dt-date" data-target-input="nearest">
        <client-only> <datepicker class="datetimepicker-input digits" v-model="date" :format="format" /></client-only>
        <div class="input-group-text" data-target="#dt-date" data-toggle="datetimepicker"><i class="fa fa-calendar"></i></div>
      </div>
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
