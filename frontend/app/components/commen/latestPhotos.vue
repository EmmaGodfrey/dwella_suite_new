<template>
  <div class="col-xl-12 col-sm-6 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5 class="p-0">
          <button
            class="btn btn-link ps-0"
            data-bs-toggle="collapse"
            data-bs-target="#collapseicon4"
            :aria-expanded="isActive ? 'true' : 'false'"
            aria-controls="collapseicon4"
            :class="[isActive ? 'active' : '', 'collapsible']"
            v-on:click="toggle"
          >
            Latest Photos
          </button>
        </h5>
      </div>
      <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
        <div class="card-body photos filter-cards-view">
          <ul>
            <li v-for="(item, index) in data" :key="index">
              <div class="latest-post"><img class="img-fluid" alt="" :src="getImages(item.img)" /></div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useProjectStore } from '~/store/project';

const store = useProjectStore();
const { latest } = storeToRefs(store);
const data = latest.value;
const isActive = ref<boolean>(true);
function toggle() {
  isActive.value = !isActive.value;
}
</script>
