<template>
  <div class="row">
    <div class="col-xl-6 box-col-6">
      <p class="pb-4">About 6,000 results (0.60 seconds)</p>
      <div class="info-block" v-for="(item, index) in data" :key="index">
        <h6>{{ item.title }}</h6>
        <a href="javascript:void(0)">{{ item.link }}</a>
        <p>{{ item.desc }}</p>
        <div class="star-ratings">
          <ul class="search-info">
            <li>3 stars</li>
            <li>590 votes</li>
            <li>Music</li>
          </ul>
        </div>
      </div>
      <div class="info-block" v-for="(item, index) in data1" :key="index">
        <h6>{{ item.title }}</h6>
        <a href="javascript:void(0)">{{ item.link }}</a>
        <p>{{ item.desc }}</p>
        <div class="star-ratings">
          <ul class="search-info">
            <li>
              <ul class="rating">
                <li><i class="icofont" :class="item.rating"></i></li>
                <li><i class="icofont" :class="item.rating"></i></li>
                <li><i class="icofont" :class="item.rating"></i></li>
                <li><i class="icofont" :class="item.rating1"></i></li>
                <li><i class="icofont" :class="item.rating1"></i></li>
              </ul>
            </li>
            <li>3 stars</li>
            <li>590 votes</li>
            <li>Music</li>
          </ul>
        </div>
      </div>
      <SearchPaginationView />
    </div>
    <div class="col-xl-6 box-col-6 search-banner">
      <div class="card">
        <div class="blog-box blog-shadow">
          <div class="blog-details">
            <p class="digits">25 July 2023</p>
            <h4>Huge part of it is the incomparable beauty you can encounter every day.</h4>
            <ul class="blog-social digits">
              <li><i class="icofont icofont-user"></i>Mark Jecno</li>
              <li><i class="icofont icofont-thumbs-up"></i>02 Hits</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useSearchStore } from '~/store/search';

const store = useSearchStore();
const { data, data1 } = storeToRefs(store);
</script>
