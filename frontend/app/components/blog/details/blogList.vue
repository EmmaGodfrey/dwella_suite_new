<template>
  <div class="col-xxl-6 set-col-12 box-col-50 xl-60">
    <div class="row">
      <div class="col-xl-12 col-md-6" v-for="(item, index) in list" :key="index">
        <div class="card">
          <div class="blog-box blog-list row">
            <div class="col-xl-6 col-12">
              <div class="blog-wrraper">
                <nuxt-link to="/blog/single"><img class="img-fluid sm-100-wp p-0" :src="getImages(item.img)" alt="" /></nuxt-link>
              </div>
            </div>
            <div class="col-xl-6 col-12">
              <div class="blog-details">
                <div class="blog-date">
                  <span>{{ item.date }}</span> {{ item.month }}
                </div>
                <nuxt-link to="/learning/details/1">
                  <h6>{{ item.title }}</h6>
                </nuxt-link>

                <div class="blog-bottom-content">
                  <ul class="blog-social">
                    <li>by: Admin</li>
                    <li>{{ item.hits }} Hits</li>
                  </ul>
                  <hr />
                  <p class="mt-0">{{ item.desc }}</p>
                </div>
              </div>
            </div>
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
const { list } = storeToRefs(store);
</script>
