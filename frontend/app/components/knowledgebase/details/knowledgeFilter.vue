<template>
  <div class="col-xl-3 xl-40 box-col-40">
    <div class="job-sidebar">
      <a class="btn btn-primary job-toggle" href="javascript:void(0)" @click="collapseFilter()">Knowledge filter</a>
      <div class="custom-scrollbar custom-scrollbar" :class="filtered ? 'open' : ''">
        <div class="default-according style-1 faq-accordion job-accordion" id="accordionoc">
          <div class="row">
            <div class="col-xl-12">
              <div class="card">
                <div class="card-header">
                  <h5 class="mb-0 p-0">
                    <button
                      class="btn btn-link ps-0"
                      data-bs-toggle="collapse"
                      :aria-expanded="isActive ? 'true' : 'false'"
                      data-bs-target="#collapseicon1"
                      :class="[isActive ? 'active' : '', 'collapsible']"
                      v-on:click="toggle"
                    >
                      Knowledge Categories
                    </button>
                  </h5>
                </div>
                <div :class="[isActive ? 'block' : 'none', 'content']" v-show="isActive">
                  <div class="categories">
                    <div class="learning-header"><span class="f-w-600">Design</span></div>
                    <ul>
                      <li><a href="javascript:void(0)">UI Design </a><span class="badge badge-primary pull-right">28</span></li>
                      <li><a href="javascript:void(0)">UX Design </a><span class="badge badge-primary pull-right">35</span></li>
                      <li><a href="javascript:void(0)">Interface Design </a><span class="badge badge-primary pull-right">17</span></li>
                      <li><a href="javascript:void(0)">User Experience </a><span class="badge badge-primary pull-right">26</span></li>
                    </ul>
                  </div>
                  <div class="categories pt-0">
                    <div class="learning-header"><span class="f-w-600">Development</span></div>
                    <ul>
                      <li><a href="javascript:void(0)">Frontend Development</a><span class="badge badge-primary pull-right">48</span></li>
                      <li><a href="javascript:void(0)">Backend Development</a><span class="badge badge-primary pull-right">19</span></li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            <KnowledgebaseDetailsUpcomingCourses />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const isActive = ref<boolean>(true);
const filtered = ref<boolean>(false);

function toggle() {
  isActive.value = !isActive.value;
}
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
