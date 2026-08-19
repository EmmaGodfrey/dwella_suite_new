s
<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h4>Status Indicator</h4>
      </div>
      <div class="card-body">
        <div class="avatar-showcase">
          <div class="avatars">
            <div class="avatar">
              <img class="img-100 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-100"></div>
            </div>
            <div class="avatar">
              <img class="img-90 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-90"></div>
            </div>
            <div class="avatar">
              <img class="img-80 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-80"></div>
            </div>
            <div class="avatar">
              <img class="img-70 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-70"></div>
            </div>
            <div class="avatar">
              <img class="img-60 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-60"></div>
            </div>
            <div class="avatar">
              <img class="img-50 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-50"></div>
            </div>
            <div class="avatar">
              <img class="img-40 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-40"></div>
            </div>
            <div class="avatar">
              <img class="img-30 rounded-circle" :src="getImages('user/3.jpg')" alt="#" />
              <div class="status status-30"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
