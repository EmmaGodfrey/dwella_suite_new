<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h4>Ratio</h4>
      </div>
      <div class="card-body">
        <div class="avatar-showcase">
          <div class="avatars">
            <div class="avatar ratio"><img class="b-r-8 img-100" :src="getImages('user/7.jpg')" alt="#" /></div>
            <div class="avatar ratio"><img class="b-r-8 img-90" :src="getImages('user/7.jpg')" alt="#" /></div>
            <div class="avatar ratio"><img class="b-r-8 img-80" :src="getImages('user/7.jpg')" alt="#" /></div>
            <div class="avatar ratio"><img class="b-r-8 img-70" :src="getImages('user/7.jpg')" alt="#" /></div>
            <div class="avatar ratio"><img class="b-r-8 img-60" :src="getImages('user/7.jpg')" alt="#" /></div>
            <div class="avatar ratio"><img class="b-r-8 img-50" :src="getImages('user/7.jpg')" alt="#" /></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
