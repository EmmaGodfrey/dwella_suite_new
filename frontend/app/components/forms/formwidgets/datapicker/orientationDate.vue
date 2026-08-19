<template>
  <div class="mb-3 row g-3">
    <label class="col-sm-3 col-form-label text-end">Orientation</label>
    <div class="col-xl-5 col-sm-9">
      <div class="form-row">
        <div class="col-md-12 mb-2">
          <client-only>
            <datepicker class="datepicker-here digits" v-model="date" position="left" placeholder="top left" />
          </client-only>
        </div>
        <div class="col-md-12 mb-2">
          <client-only>
            <datepicker class="datepicker-here digits" v-model="date1" position="right" placeholder="top right" />
          </client-only>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const date = ref();
const date1 = ref();
</script>
