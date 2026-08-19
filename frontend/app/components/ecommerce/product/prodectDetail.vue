<template>
  <div class="product-wrapper-grid" :class="listViewEnable ? 'list-view' : ''">
    <div class="row">
      <div
        :class="[
          col2 ? 'col-md-6' : col3 ? 'col-xl-4 col-sm-4' : col4 ? 'col-xl-3 col-md-6' : col6 ? 'col-xl-2 col-lg-4 col-md-6' : list ? 'col-xl-3 col-lg-4 col-sm-6 xl-25 col-xl-12' : 'col-xl-3 col-md-6',
        ]"
        v-for="(product, index) in filterProducts"
        :key="index"
      >
        <div class="card">
          <div class="product-box">
            <div class="product-img">
              <div class="ribbon ribbon-danger" v-if="product.sale">Sale</div>
              <div class="ribbon ribbon-success ribbon-right" v-if="product.off">50%</div>
              <img class="img-fluid" :src="getImgUrl(product.images[0] ?? '')" />
              <div class="product-hover">
                <ul>
                  <nuxt-link :to="'/ecommerce/cart'">
                    <li @click="addToCart(product)">
                      <i class="icon-shopping-cart"> </i>
                    </li>
                  </nuxt-link>
                  <a data-bs-toggle="modal" data-bs-target="#exampleModal">
                    <li @click="quickView(product)">
                      <i class="icon-eye"> </i>
                    </li>
                  </a>
                </ul>
              </div>
            </div>
            <EcommerceProductModel :quickViewProduct="quickViewProduct" />
            <div class="product-details">
              <nuxt-link :to="'/ecommerce/details/' + product.sku">
                <h4>{{ product.name }}</h4>
              </nuxt-link>
              <p>{{ product.shortDescription }}</p>
              <div class="product-price">
                ${{ product.price }}
                <del>${{ product.salePrice }}</del>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { storeToRefs } from 'pinia';

import { useProductsStore } from '~/store/products';
import type { product } from '~/types/products';

const modalShow = ref<boolean>(false);
const store = useProductsStore();
let { filterProducts, col2, col3, col4, col6, list, listViewEnable } = storeToRefs(store);
let { addToCart } = store;

const quickViewProduct = ref<product | null>(null);
function quickView(Product: product) {
  modalShow.value = true;
  return (quickViewProduct.value = Product);
}
function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>
