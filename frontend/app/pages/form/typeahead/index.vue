<template>
  <TheBreadcrumbs sub="Forms" main="Form Widgets" title="Typeahead" />
  <div class="container-fluid">
    <div class="typeahead">
      <div class="row">
        <FormsFormwidgetsTypeaheadBasicTypeahead />
        <FormsFormwidgetsTypeaheadPrefetchTypeahead />
        <FormsFormwidgetsTypeaheadBloodhoundTyeahead />
        <FormsFormwidgetsTypeaheadRemoteTypeahead />
        <FormsFormwidgetsTypeaheadCustomTemplates />
        <FormsFormwidgetsTypeaheadMultipleSections />
        <FormsFormwidgetsTypeaheadDefaultView />
        <FormsFormwidgetsTypeaheadScrollableMenu />
        <FormsFormwidgetsTypeaheadRtlSupport />
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
useHead({
  title: 'Form Widgets Typeahead | Cion - Premium Vue Admin Template',
});
</script>
