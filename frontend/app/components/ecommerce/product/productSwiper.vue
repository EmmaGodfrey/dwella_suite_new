<template>
  <swiper :loop="true" :rewind="true">
    <swiper-slide>
      <div class="product-box row" v-for="(product, index) in products.slice(0, 3)" :key="index">
        <div class="product-img col-md-6 mb-3">
          <img class="img-fluid" :src="getImages(product.images[0] ?? '')" alt="" />
        </div>
        <div class="product-details col-md-6 text-start">
          <span>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning"></i>
          </span>
          <nuxt-link :to="'/ecommerce/details/' + product.sku">
            <p class="mb-0">{{ product.name }}</p>
          </nuxt-link>
          <div class="product-price">{{ product.price }}</div>
        </div>
      </div>
    </swiper-slide>
    <swiper-slide v-if="products.length >= 4">
      <div class="product-box row" v-for="(product, index) in products.slice(3, 6)" :key="index">
        <div class="product-img col-md-6 mb-3">
          <img class="img-fluid" :src="getImages(product.images[0] ?? '')" alt="" />
        </div>
        <div class="product-details col-md-6 text-start">
          <span>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning me-1"></i>
            <i class="fa fa-star font-warning"></i>
          </span>
          <nuxt-link :to="'/ecommerce/details/' + product.sku">
            <p class="mb-0">{{ product.name }}</p>
          </nuxt-link>
          <div class="product-price">{{ product.price }}</div>
        </div>
      </div>
    </swiper-slide>
  </swiper>
</template>
<script lang="ts" setup>
import { Swiper, SwiperSlide } from 'swiper/vue';

import { getImages } from '~/composables/commen/imgMixin';
import { useProductsStore } from '~/store/products';
import 'swiper/css';

const store = useProductsStore();
const { products } = storeToRefs(store);
</script>
