<template>
  <div class="col-xl-3 box-col-3">
    <div class="job-sidebar">
      <a class="btn btn-primary job-toggle" href="javascript:void(0)" @click="collapseFilter()">learning filter</a>
      <div class="job-left-aside custom-scrollbar" :class="filtered ? 'open' : ''">
        <div class="default-according style-1 job-accordion" id="accordionoc">
          <div class="row">
            <LearningLearningfilterFindCourse />
            <LearningLearningfilterCategoriesView />
            <LearningLearningfilterUpcomingCourses />
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
