<template>
  <TheBreadcrumbs sub="Forms" main="Form Widgets" title="Time Picker" />
  <div class="container-fluid date-time">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Date Time Picker</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-12">
            <div class="datetime-picker">
              <form class="theme-form">
                <FormsFormwidgetsDatetimepickerUsingLocales />
                <FormsFormwidgetsDatetimepickerTimeOnly />
                <FormsFormwidgetsDatetimepickerDateOnly />
                <FormsFormwidgetsDatetimepickerNoIcon />
                <FormsFormwidgetsDatetimepickerDisableDay />
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
  title: 'Form Widgets Date Time Picker| Cion - Premium Vue Admin Template',
});
</script>
