<template>
  <div class="col-xl-5 col-md-6 box-col-12 xl-50">
    <div class="card">
      <div class="card-body">
        <div class="row">
          <div class="col-xl-9 product-main">
            <div class="pro-slide-single">
              <ClientOnly>
                <Swiper
                  :slidesPerView="1"
                  :loop="true"
                  :thumbs="{ swiper: thumbsSwiper }"
                  :autoplay="{ delay: 3500, disableOnInteraction: false }"
                  :spaceBetween="30"
                  :centeredSlides="true"
                  :modules="modules"
                  class="mySwiper"
                >
                  <Swiper-slide v-for="(product, index) in product?.images" :key="index">
                    <img :src="getImgUrl(product)" class="img-fluid bg-img" alt="index" />
                  </Swiper-slide>
                </Swiper>
              </ClientOnly>
            </div>
          </div>
          <div class="col-xl-3 product-thumbnail">
            <div class="pro-slide-right">
              <div>
                <ClientOnly>
                  <Swiper
                    :breakpoints="swiperOptions"
                    @swiper="setThumbsSwiper"
                    :loop="true"
                    :autoHeight="true"
                    :slidesPerView="3"
                    :spaceBetween="3"
                    :watchSlidesProgress="true"
                    :pagination="{
                      clickable: true,
                    }"
                    :modules="modules"
                    class="Swiper"
                  >
                    <Swiper-slide v-for="(product, index) in product?.images" :key="index">
                      <img :src="getImgUrl(product)" class="img-fluid bg-img" alt="index" style="height: auto" />
                    </Swiper-slide>
                  </Swiper>
                </ClientOnly>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import type { Swiper as SwiperClass, SwiperOptions } from 'swiper';
import { Autoplay, FreeMode, Navigation, Thumbs } from 'swiper';
import { Swiper, SwiperSlide } from 'swiper/vue';
import { useRoute } from 'vue-router';

import 'swiper/css/free-mode';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';
import 'swiper/css/thumbs';
import { useProductsStore } from '~/store/products';

const thumbsSwiper = ref<SwiperClass | null>(null);
const route = useRoute();
const store = useProductsStore();
const { products } = storeToRefs(store);
const setThumbsSwiper = (swiper: SwiperClass) => {
  thumbsSwiper.value = swiper;
};
const product = products.value.find(item => parseInt(route.params.id as string) === item.sku);
const modules = [Autoplay, Navigation, FreeMode, Thumbs];

const swiperOptions: { [width: number]: SwiperOptions } = {
  1215: {
    direction: 'vertical',
  },
};
function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>
