<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header">
        <h5 class="p-0">
          <button
            class="btn btn-link ps-0"
            data-bs-toggle="collapse"
            data-bs-target="#collapseicon12"
            :aria-expanded="isActive ? 'true' : 'false'"
            aria-controls="collapseicon12"
            :class="[isActive ? 'active' : '', 'collapsible']"
            v-on:click="toggle"
          >
            Activity Feed
          </button>
        </h5>
      </div>
      <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
        <div class="card-body social-status filter-cards-view">
          <div class="media align-items-center" v-for="(friend, index) in friends" :key="index">
            <img class="img-50 rounded-circle m-r-15" :src="getImages(friend.image)" alt="" />
            <div class="media-body">
              <nuxt-link to="/users/profile">
                <span class="f-w-600 d-block">{{ friend.name }}</span></nuxt-link
              >
              <p>Commented on Shaun Park's <a href="javascript:void(0)">Photo</a></p>
              <span class="light-span">20 min Ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useSocialStore } from '~/store/social';

const isActive = ref<boolean>(true);
const store = useSocialStore();
const { activity } = storeToRefs(store);
const friends = activity.value;
function toggle() {
  isActive.value = !isActive.value;
}
</script>
