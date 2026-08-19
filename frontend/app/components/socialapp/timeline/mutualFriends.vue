<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header">
        <h5 class="p-0">
          <button
            class="btn btn-link ps-0"
            data-bs-toggle="collapse"
            data-bs-target="#collapseicon1"
            :aria-expanded="isActive ? 'true' : 'false'"
            aria-controls="collapseicon1"
            :class="[isActive ? 'active' : '', 'collapsible']"
            v-on:click="toggle"
          >
            Mutual Friends
          </button>
        </h5>
      </div>
      <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
        <div class="card-body social-status filter-cards-view">
          <form>
            <div class="form-group m-0">
              <input class="form-control-social" type="search" placeholder="Search Contacts.." />
            </div>
          </form>
          <div class="media align-items-center" v-for="(friend, index) in friends" :key="index">
            <img class="img-50 rounded-circle m-r-15" :src="getImages(friend.image)" alt="" />
            <div class="social-status" :class="friend.StatusClass"></div>
            <div class="media-body">
              <nuxt-link to="/users/profile">
                <span class="f-w-600 d-block">{{ friend.name }}</span></nuxt-link
              ><span class="d-block">{{ friend.email }}</span>
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
const { data } = storeToRefs(store);
const friends = data.value;
function toggle() {
  isActive.value = !isActive.value;
}
</script>
