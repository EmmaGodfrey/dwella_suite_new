<template>
  <div class="col-xl-5 box-col-6 proorder-xl-3 xl-100">
    <div class="card">
      <div class="card-body">
        <div class="pro-group pt-0 border-0">
          <div class="product-page-details mt-0">
            <h3>{{ product?.name }}</h3>
            <div class="pro-review">
              <div class="d-flex">
                <ClientOnly>
                  <star-rating :show-rating="false" :star-size="20" :max-rating="5" :increment="0.01"></star-rating>
                </ClientOnly>
              </div>
            </div>
          </div>
          <div class="product-price">
            ${{ product?.price }}
            <del>${{ product?.salePrice }}</del>
          </div>
          <div class="color-selector">
            <ul class="product-color">
              <li class="bg-primary"></li>
              <li class="bg-secondary"></li>
              <li class="bg-success"></li>
              <li class="bg-danger"></li>
              <li class="bg-info"></li>
              <li class="bg-warning"></li>
            </ul>
          </div>
          <nuxt-link class="btn btn-secondary mt-0" to="/ecommerce/cart" @click="product && addToCart(product)"><i class="fa fa-shopping-cart me-2"></i>Buy Now</nuxt-link>
        </div>
        <div class="pro-group">
          <p>{{ product?.description }}</p>
        </div>
        <EcommerceProductpageStockView />
        <div class="pro-group">
          <div class="row">
            <div class="col-md-4 xl-50 box-col-30">
              <h6 class="product-title">share it</h6>
            </div>
            <div class="col-md-7 xl-50 box-col-70">
              <div class="product-icon">
                <ul class="product-social">
                  <li class="d-inline-block">
                    <a href="https://www.facebook.com" target="_blank"><i class="fa fa-facebook"></i></a>
                  </li>
                  <li class="d-inline-block">
                    <a href="https://www.google.com/" target="_blank"><i class="fa fa-google-plus"></i></a>
                  </li>
                  <li class="d-inline-block">
                    <a href="https://twitter.com/" target="_blank"><i class="fa fa-twitter"></i></a>
                  </li>
                  <li class="d-inline-block">
                    <a href="https://www.instagram.com/" target="_blank"><i class="fa fa-instagram"> </i></a>
                  </li>
                  <li class="d-inline-block">
                    <a href="https://dashboard.rss.com/auth/sign-in"><i class="fa fa-rss"></i></a>
                  </li>
                </ul>
                <form class="d-inline-block f-right"></form>
              </div>
            </div>
          </div>
        </div>
        <div class="pro-group pb-0">
          <div class="pro-shop">
            <nuxt-link :to="'/ecommerce/cart'" class="btn btn-primary m-r-10" @click="product && addToCart(product)"> <i class="fa fa-shopping-basket me-2"></i>Add To Cart</nuxt-link>
            <nuxt-link :to="'/ecommerce/wishList'" class="btn btn-danger"><i class="fa fa-heart me-2"></i>Add To WishList</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useRoute } from 'vue-router';

import { useProductsStore } from '~/store/products';

let route = useRoute();
const store = useProductsStore();
const { products } = storeToRefs(store);
const { addToCart } = store;
const product = products.value.find(item => parseInt(route.params.id as string) === item.sku);
</script>
