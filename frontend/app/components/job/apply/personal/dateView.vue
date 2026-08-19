<template>
  <div class="col-xl-6 xl-100 xl-mt-job">
    <label class="col-form-label text-end pt-0">Period:<span class="font-danger">*</span></label>
    <div class="row">
      <div class="col-sm-6">
        <client-only> <datepicker placeholder="Start Date" class="datepicker-here digits" v-model="date" :format="format" /></client-only>
      </div>
      <div class="col-sm-6 xs-mt-period">
        <client-only> <datepicker placeholder="End Date" class="datepicker-here digits" v-model="date1" :format="format" /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date = ref<Date | null>(null);
const date1 = ref<Date | null>(null);
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
