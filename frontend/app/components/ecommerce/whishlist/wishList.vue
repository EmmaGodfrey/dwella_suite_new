<template>
  <div class="col-xl-2 box-col-3 col-md-4 col-sm-6" v-for="(cards, index) in wishlist" :key="index">
    <div class="prooduct-details-box">
      <div class="media">
        <nuxt-link to="/ecommerce/details/1"><img class="align-self-center img-fluid" :src="getImgUrl(cards.img)" alt="#" /></nuxt-link>
        <div class="media-body">
          <div class="product-name">
            <nuxt-link to="/ecommerce/details/1">
              <h6>{{ cards.name }}</h6>
            </nuxt-link>
          </div>
          <ul class="rating">
            <li><i class="fa fa-star"></i></li>
            <li><i class="fa fa-star"></i></li>
            <li><i class="fa fa-star"></i></li>
            <li><i class="fa" :class="cards.star1"></i></li>
            <li><i class="fa" :class="cards.star2"></i></li>
          </ul>
          <div class="price">
            Price<span>: {{ cards.price }}$</span>
          </div>
          <div class="avaiabilty">
            <div :class="cards.color">{{ cards.stock }}</div>
          </div>
          <nuxt-link to="/ecommerce/cart" class="btn btn-primary btn-xs">Move to Cart</nuxt-link>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useInvoiceStore } from '~/store/invoice';

const store = useInvoiceStore();
const { wishlist } = storeToRefs(store);

function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>
