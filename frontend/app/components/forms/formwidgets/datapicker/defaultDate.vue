<template>
  <div class="form-group row">
    <label class="col-sm-3 col-form-label text-end">Default</label>
    <div class="col-xl-5 col-sm-9">
      <client-only>
        <datepicker class="datepicker-here digits" v-model="date" :format="format" />
      </client-only>
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
