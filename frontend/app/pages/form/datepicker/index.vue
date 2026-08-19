<template>
  <TheBreadcrumbs sub="Forms" main="Form Widgets" title="Datepicker" />
  <div class="container-fluid">
    <div class="card">
      <div class="card-header">
        <h5>Date Picker</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-12">
            <div class="date-picker">
              <form class="theme-form">
                <FormsFormwidgetsDatapickerDefaultDate />
                <FormsFormwidgetsDatapickerMultipleDate />
                <FormsFormwidgetsDatapickerMonthDate />
                <FormsFormwidgetsDatapickerMinimumMaximum />
                <FormsFormwidgetsDatapickerRangeDate />
                <FormsFormwidgetsDatapickerDisableDate />
                <FormsFormwidgetsDatapickerOrientationDate />
                <FormsFormwidgetsDatapickerPermanentlyVisible />
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Form Widgets Datepicker | Cion - Premium Vue Admin Template',
});
</script>
