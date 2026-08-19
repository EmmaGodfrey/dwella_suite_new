<template>
  <div class="col-sm-6 col-xl-3 box-col-6 des-xl-50" v-for="(item, index) in details" :key="index">
    <div class="card">
      <div class="blog-box blog-grid">
        <div class="blog-wrraper">
          <nuxt-link to="/blog/single"> <img class="img-fluid top-radius-blog" :src="getImages(item.imge)" alt="" /></nuxt-link>
        </div>
        <div class="blog-details-second">
          <div class="blog-post-date"><span class="blg-month">apr</span><span class="blg-date">10</span></div>
          <nuxt-link to="/users/edit">
            <h6 class="blog-bottom-details">{{ item.title }}</h6>
          </nuxt-link>

          <p>{{ item.desc }}.</p>
          <div class="detail-footer">
            <ul class="sociyal-list">
              <li><i class="fa fa-user-o"></i>Admin</li>
              <li><i class="fa fa-comments-o"></i>{{ item.comment }}</li>
              <li><i class="fa fa-thumbs-o-up"></i>{{ item.like }} like</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useBlogStore } from '~/store/blog';

const store = useBlogStore();
const { data } = storeToRefs(store);
const details = data.value;
</script>
