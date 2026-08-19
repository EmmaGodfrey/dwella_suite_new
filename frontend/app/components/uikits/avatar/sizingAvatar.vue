<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h4>Sizing</h4>
      </div>
      <div class="card-body">
        <div class="avatar-showcase">
          <div class="avatars">
            <div class="avatar"><img class="img-100 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-90 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-80 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-70 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-60 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-50 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-40 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-30 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
            <div class="avatar"><img class="img-20 rounded-circle" :src="getImages('user/1.jpg')" alt="#" /></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
