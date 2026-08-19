<template>
  <div class="col-md-9 col-sm-10 text-end">
    <span class="f-w-600 m-r-5">Showing Products 1 - {{ filterProducts.length }} Results</span>
    <div class="select2-drpdwn-product select-options d-inline-block">
      <select class="form-control btn-square" name="select" @change="onChangeSort($event)">
        <option value="opt1">Lowest Prices</option>
        <option value="opt2">Highest Prices</option>
        <option value="opt3">Featured</option>
      </select>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

const store = useProductsStore();
const { filterProducts } = storeToRefs(store);
const { sortProducts } = store;
function onChangeSort(event: Event) {
  const target = event.target as HTMLSelectElement;
  sortProducts(target.value);
}
</script>
