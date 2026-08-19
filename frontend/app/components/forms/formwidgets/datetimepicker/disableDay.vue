<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">Disabled Days of the Week</label>
    <div class="col-xl-5 col-sm-7 col-lg-8">
      <div class="input-group date" id="dt-enab-disab-date" data-target-input="nearest">
        <client-only> <datepicker class="digits" v-model="date" :disabledDates="disabledDates" /></client-only>
        <div class="input-group-text" data-target="#dt-enab-disab-date" data-toggle="datetimepicker"><i class="fa fa-calendar"></i></div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date = ref(new Date());

const disabledDates = computed(() => {
  const today = new Date();

  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const afterTomorrow = new Date(tomorrow);
  afterTomorrow.setDate(tomorrow.getDate() + 1);

  return [tomorrow, afterTomorrow];
});
</script>
