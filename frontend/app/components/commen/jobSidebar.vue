<template>
  <div class="col-xl-3 xl-40 box-col-4">
    <div class="job-sidebar">
      <a class="btn btn-primary job-toggle" @click="collapseFilter()" href="javascript:void(0)">job filter</a>
      <div class="job-left-aside custom-scrollbar" :class="filtered ? 'open' : ''">
        <div class="default-according style-1 faq-accordion job-accordion" id="accordionoc">
          <div class="row">
            <JobJobfilterFilterView />
            <JobJobfilterLocationView />
            <JobJobfilterJobTitle />
            <JobJobfilterIndustryView />
            <JobJobfilterSpecificSkills />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const filtered = ref<boolean>(false);
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
