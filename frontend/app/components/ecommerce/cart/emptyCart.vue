<template>
  <div class="col-sm-12 empty-cart-cls text-center" v-if="!cart.length">
    <img :src="getImgUrl('ecommerce/icon-empty-cart.png')" class="img-fluid mb-4" />
    <h3><strong>Your Cart is Empty</strong></h3>
    <h4>Add something to make me happy :)</h4>
    <nuxt-link :to="'/ecommerce/product'" class="btn btn-primary cart-btn-transform m-t-15">continue shopping</nuxt-link>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

const store = useProductsStore();
const { cart } = storeToRefs(store);

function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>
