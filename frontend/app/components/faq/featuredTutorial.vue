<template>
  <div class="col-lg-12 featured-tutorial">
    <div class="header-faq">
      <h5 class="mb-0">Featured Tutorials</h5>
    </div>
    <div class="row">
      <div class="col-xl-3 col-sm-6 box-col-3" v-for="(item, index) in faq" :key="index">
        <div class="card features-faq product-box">
          <div class="faq-image product-img">
            <img class="img-fluid" :src="getImages(item.imge)" alt="" />
            <div class="product-hover">
              <ul>
                <li><i class="icon-link"></i></li>
                <li><i class="icon-import"></i></li>
              </ul>
            </div>
          </div>
          <div class="card-body">
            <nuxt-link to="/learning/details/1">
              <h6>{{ item.title }}</h6>
            </nuxt-link>
            <p>{{ item.desc }}</p>
          </div>
          <div class="card-footer">
            <span>{{ item.date }}</span>
            <ul class="rating pull-right">
              <li><i class="fa fa-star font-primary"></i></li>
              <li><i class="fa fa-star font-primary"></i></li>
              <li><i class="font-primary fa" :class="item.star"></i></li>
              <li><i class="font-primary fa" :class="item.star1"></i></li>
              <li><i class="font-primary fa" :class="item.star2"></i></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useFaqStore } from '~/store/faq';

const store = useFaqStore();
const { data } = storeToRefs(store);
const faq = data.value;
</script>
