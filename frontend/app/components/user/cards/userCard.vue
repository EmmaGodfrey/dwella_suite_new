<template>
  <div class="col-md-6 col-lg-6 col-xl-4 box-col-6" v-for="(item, index) in friendItem" :key="index">
    <div class="card custom-card">
      <div class="card-header"><img class="img-fluid" :src="getImages(item.img)" alt="" /></div>
      <div class="card-profile"><img class="rounded-circle" :src="getImages(item.img1)" alt="" /></div>

      <ul class="card-social">
        <li>
          <a href="https://www.facebook.com" target="_blank"><i class="fa fa-facebook"></i></a>
        </li>
        <li>
          <a href="https://accounts.google.com" target="_blank"><i class="fa fa-google-plus"></i></a>
        </li>
        <li>
          <a href="https://twitter.com" target="_blank"><i class="fa fa-twitter"></i></a>
        </li>
        <li>
          <a href="https://www.instagram.com" target="_blank"><i class="fa fa-instagram"></i></a>
        </li>
        <li>
          <a href="https://dashboard.rss.com/auth/sign-in" target="_blank"><i class="fa fa-rss"></i></a>
        </li>
      </ul>
      <div class="text-center profile-details">
        <nuxt-link to="/users/profile">
          <h4>{{ item.name }}</h4>
        </nuxt-link>
        <h6>{{ item.title }}</h6>
      </div>
      <div class="card-footer row">
        <div class="col-4 col-sm-4">
          <h6>Follower</h6>
          <h3 class="counter">{{ item.follower }}</h3>
        </div>
        <div class="col-4 col-sm-4">
          <h6>Following</h6>
          <h3>
            <span class="counter">{{ item.following }}</span
            >K
          </h3>
        </div>
        <div class="col-4 col-sm-4">
          <h6>Total Post</h6>
          <h3>
            <span class="counter">{{ item.total }}</span
            >M
          </h3>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useUserStore } from '~/store/usercard';

const store = useUserStore();
const { data } = storeToRefs(store);
const friendItem = data.value;
</script>
