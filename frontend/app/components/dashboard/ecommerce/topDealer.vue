<template>
  <div class="col-xl-6 box-col-12 des-xl-100 top-dealer-sec">
    <div class="card">
      <div class="card-header pb-0">
        <div class="header-top d-sm-flex justify-content-between align-items-center">
          <h5>Top Dealer</h5>
          <div class="center-content">
            <p class="d-sm-flex align-items-center"><span class="m-r-10">845 Dealer</span><i class="toprightarrow-primary fa fa-arrow-up m-r-10 d-grid"></i>86% More Than Last Year</p>
          </div>
        </div>
      </div>
      <div class="card-body pb-3">
        <div class="col-12">
          <div class="row">
            <swiper :space-between="10" :breakpoints="swiperOptions" :slidesPerView="4" @swiper="setSecondSwiper" :controller="{ control: firstSwiper || undefined }" :modules="modules" :loop="true">
              <swiper-slide v-for="(card, index) in cards" :key="index">
                <div class="item">
                  <div class="card">
                    <div class="top-dealerbox text-center">
                      <img class="card-img-top" :src="getImages(card.src1)" alt="..." />
                      <h6>{{ card.name }}</h6>
                      <p>{{ card.name1 }}</p>
                      <nuxt-link to="/pages/social_app" class="btn btn-rounded">View More</nuxt-link>
                    </div>
                  </div>
                </div>
              </swiper-slide>
            </swiper>
            <swiper
              :space-between="10"
              :pagination="{
                clickable: true,
              }"
              :slidesPerView="4"
              :modules="modules"
              @swiper="setFirstSwiper"
              :breakpoints="swiperOptions"
              :controller="{ control: secondSwiper || undefined }"
              :loop="true"
            >
              <swiper-slide v-for="(card, index) in card1" :key="index">
                <div class="item">
                  <div class="card">
                    <div class="top-dealerbox text-center">
                      <img class="card-img-top" :src="getImages(card.src1)" alt="..." />
                      <h6>{{ card.name }}</h6>
                      <p>{{ card.name1 }}</p>
                      <nuxt-link to="/pages/social_app" class="btn btn-rounded">View More</nuxt-link>
                    </div>
                  </div>
                </div>
              </swiper-slide>
            </swiper>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import type { Swiper as SwiperType } from 'swiper';
import { Autoplay, FreeMode, Navigation, Thumbs, Pagination, Controller } from 'swiper';
import { Swiper, SwiperSlide } from 'swiper/vue';

import { getImages } from '~/composables/commen/imgMixin';
import { useDashboardStore } from '~/store/dashboard';

import 'swiper/css';
import 'swiper/css/pagination';

const firstSwiper = ref<SwiperType | null>(null);
const secondSwiper = ref<SwiperType | null>(null);
const store = useDashboardStore();
const { cards } = storeToRefs(store);
const card1 = cards.value;
const swiperOptions = {
  0: {
    slidesPerView: 2,
  },
  480: {
    slidesPerView: 3,
  },
  1669: {
    slidesPerView: 4,
  },
};
const modules = [Autoplay, Navigation, FreeMode, Thumbs, Pagination, Controller];

const setFirstSwiper = (swiper: SwiperType) => {
  firstSwiper.value = swiper;
};
const setSecondSwiper = (swiper: SwiperType) => {
  secondSwiper.value = swiper;
};
</script>
