<template>
  <div class="col-xl-12 col-sm-6 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5 class="p-0">
          <button
            class="btn btn-link ps-0"
            data-bs-toggle="collapse"
            data-bs-target="#collapseicon13"
            aria-expanded="true"
            aria-controls="collapseicon13"
            :class="[isActive ? 'active' : '', 'collapsible']"
            v-on:click="toggle"
          >
            Friends
          </button>
        </h5>
      </div>
      <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
        <div class="card-body avatar-showcase filter-cards-view">
          <div class="d-inline-block friend-pic" v-for="(item, index) in data" :key="index"><img class="img-50 rounded-circle" :src="getImages(item.img)" alt="#" /></div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useProjectStore } from '~/store/project';

const isActive = ref<boolean>(true);
const store = useProjectStore();
const { friend } = storeToRefs(store);
const data = friend.value;

function toggle() {
  isActive.value = !isActive.value;
}
</script>
