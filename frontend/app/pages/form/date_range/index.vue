<template>
  <TheBreadcrumbs sub="Forms" main="Form Widgets" title="Date Range Picker" />
  <div class="container-fluid">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Date Range Picker</h5>
      </div>
      <div class="card-body">
        <div class="row date-range-picker">
          <FormsFormwidgetsDaterangpickerRangePicker />
          <FormsFormwidgetsDaterangpickerSingleDate />
          <FormsFormwidgetsDaterangpickerInitiallyEmpty />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Form Widgets Date Range Picker| Cion - Premium Vue Admin Template',
});
</script>
