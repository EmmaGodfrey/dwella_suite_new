<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Center Example</h5>
    </div>
    <div class="card-body">
      <div class="owl-carousel owl-theme" id="owl-carousel-3">
        <ClientOnly>
          <Swiper
            :autoHeight="true"
            :breakpoints="swiperOptions"
            :slidesPerView="1"
            :freeMode="true"
            :loop="true"
            :spaceBetween="10"
            :pagination="{
              clickable: true,
            }"
            :modules="modules"
            class="mySwiper"
          >
            <SwiperSlide v-for="(item, index) in owlCarousel" :key="index">
              <div class="item"><img :src="getImages(item.img)" alt="" /></div>
            </SwiperSlide>
          </Swiper>
        </ClientOnly>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { Pagination, FreeMode } from 'swiper';
import { Swiper, SwiperSlide } from 'swiper/vue';

import 'swiper/css';
import 'swiper/css/pagination';
import { getImages } from '~/composables/commen/imgMixin';
import { useOwlcarouselStore } from '~/store/owlcarousel';

const store = useOwlcarouselStore();
const { items } = storeToRefs(store);
const owlCarousel = items.value;
const modules = [Pagination, FreeMode];
const swiperOptions = {
  576: {
    slidesPerView: 1,
  },
  768: {
    slidesPerView: 2,
  },
  992: {
    slidesPerView: 3,
  },
};
</script>
