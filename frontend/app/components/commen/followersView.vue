<template>
  <div class="col-xl-12 col-sm-6 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5 class="p-0">
          <button
            class="btn btn-link ps-0"
            data-bs-toggle="collapse"
            data-bs-target="#collapseicon8"
            :aria-expanded="isActive ? 'true' : 'false'"
            aria-controls="collapseicon8"
            :class="[isActive ? 'active' : '', 'collapsible']"
            v-on:click="toggle"
          >
            Followers
          </button>
        </h5>
      </div>
      <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
        <div class="card-body social-list filter-cards-view">
          <div class="media" v-for="(item, index) in data" :key="index">
            <img class="img-50 img-fluid m-r-20 rounded-circle" alt="" :src="item.img" />
            <div class="media-body">
              <span class="d-block">{{ item.name }}</span
              ><a href="javascript:void(0)">{{ item.frd }}</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const isActive = ref<boolean>(true);
const store = useProjectStore();
const { follower } = storeToRefs(store);
const data = follower.value;
function toggle() {
  isActive.value = !isActive.value;
}
</script>
