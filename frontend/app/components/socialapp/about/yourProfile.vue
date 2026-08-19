<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Viewed Your Profile</h5>
      </div>
      <div class="card-body avatar-showcase pt-0">
        <div class="pepole-knows">
          <ul>
            <li v-for="(item, index) in post" :key="index">
              <div class="add-friend text-center">
                <img class="img-60 img-fluid rounded-circle" alt="" :src="getImages(item.image)" /><span class="d-block f-w-600">{{ item.name }}</span>
                <button class="btn btn-primary btn-xs">Add Friend</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useSocialStore } from '~/store/social';

const store = useSocialStore();
const { addfriend } = storeToRefs(store);
const post = addfriend.value;
</script>
