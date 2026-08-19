<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Basic Example</h5>
    </div>
    <div class="card-body">
      <div class="owl-carousel owl-theme" id="owl-carousel-1">
        <ClientOnly>
          <Swiper
            :autoHeight="true"
            :breakpoints="swiperOptions"
            :slidesPerView="5"
            :spaceBetween="10"
            :loop="true"
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
import { Pagination } from 'swiper';
import { Swiper, SwiperSlide } from 'swiper/vue';

import { getImages } from '~/composables/commen/imgMixin';
import { useOwlcarouselStore } from '~/store/owlcarousel';

const store = useOwlcarouselStore();
const { items } = storeToRefs(store);
const owlCarousel = items.value;
const modules = [Pagination];
const swiperOptions = {
  0: {
    slidesPerView: 1,
  },
  600: {
    slidesPerView: 3,
  },
  1000: {
    slidesPerView: 5,
  },
};
</script>
