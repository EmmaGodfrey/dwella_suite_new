<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header">
        <h4>Groups</h4>
      </div>
      <div class="card-body">
        <div class="avatar-showcase">
          <div class="customers d-inline-block avatar-group">
            <ul>
              <li class="d-inline-block"><img class="img-70 rounded-circle" :src="getImages('user/3.jpg')" alt="" /></li>
              <li class="d-inline-block"><img class="img-70 rounded-circle" :src="getImages('user/5.png')" alt="" /></li>
              <li class="d-inline-block"><img class="img-70 rounded-circle" :src="getImages('user/1.jpg')" alt="" /></li>
            </ul>
          </div>
          <div class="customers d-inline-block avatar-group">
            <ul>
              <li class="d-inline-block"><img class="img-50 rounded-circle" :src="getImages('user/3.jpg')" alt="" /></li>
              <li class="d-inline-block"><img class="img-50 rounded-circle" :src="getImages('user/5.png')" alt="" /></li>
              <li class="d-inline-block"><img class="img-50 rounded-circle" :src="getImages('user/1.jpg')" alt="" /></li>
            </ul>
          </div>
          <div class="customers d-inline-block avatar-group">
            <ul>
              <li class="d-inline-block"><img class="img-40 rounded-circle" :src="getImages('user/3.jpg')" alt="" /></li>
              <li class="d-inline-block"><img class="img-40 rounded-circle" :src="getImages('user/5.png')" alt="" /></li>
              <li class="d-inline-block"><img class="img-40 rounded-circle" :src="getImages('user/1.jpg')" alt="" /></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
