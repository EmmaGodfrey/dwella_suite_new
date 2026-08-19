<template>
  <TheBreadcrumbs sub="Forms" main="Form Widgets" title="Select2" />

  <div class="container-fluid">
    <div class="select2-drpdwn">
      <div class="row">
        <FormsFormwidgetsSelect2SelectView />
        <FormsFormwidgetsSelect2FullColored />
        <FormsFormwidgetsSelect2OutlineColor />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Form Widgets Select | Cion - Premium Vue Admin Template',
});
</script>
