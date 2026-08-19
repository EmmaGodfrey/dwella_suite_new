<template>
  <div class="left-filter">
    <div class="card-body filter-cards-view animate-chk">
      <div class="product-filter">
        <h6 class="f-w-600">Category</h6>
        <div class="checkbox-animated mt-0">
          <label class="d-block" for="edo-ani5" v-for="(product, index) in getCategory" :key="index">
            <input @change="appliedFilter()" :value="product.category" v-model="applyFilter" class="checkbox_animated" :id="product.category" type="checkbox" />{{ product.category }}
          </label>
        </div>
      </div>
      <div class="product-filter">
        <h6 class="f-w-600">Brand</h6>
        <div class="checkbox-animated mt-0">
          <label class="d-block" v-for="(brand, index) in getBrands" @change="$emit('allFilters', applyFilter)" :key="index">
            <input class="checkbox_animated" :value="brand" v-model="applyFilter" :id="brand" type="checkbox" />
            {{ brand }}
          </label>
        </div>
      </div>
      <div class="product-filter slider-product">
        <h6 class="f-w-600">Colors</h6>
        <div class="color-selector">
          <ul>
            <li :style="{ 'background-color': color.color }" :class="applyFilter ? '' : 'active'" v-for="(color, index) in getColors" :key="'color' + index">
              <input @change="appliedFilter()" class="colorCheckbox" :value="color.color" v-model="applyFilter" :id="color.color" type="checkbox" />
              <div class="colorDiv"></div>
            </li>
          </ul>
        </div>
      </div>
      <div class="product-filter pb-0">
        <h6 class="f-w-500">Price</h6>
        <ClientOnly>
          <VueSlider v-model="one.value" :data="one.data1" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"> </VueSlider>
        </ClientOnly>
        <h6 class="f-w-600 mt-5">New Products</h6>
      </div>
      <div class="product-filter pb-0 new-products">
        <EcommerceProductSwiper />
      </div>
      <div class="product-filter text-center"><img class="img-fluid banner-product" src="/images/ecommerce/banner.jpg" alt="" data-original-title="" title="" /></div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

interface slider {
  value: number[];
  data1: number[];
}
const range = ref<number[]>([0, 900]);
const applyFilter = ref<object>([]);
const one = ref<slider>({
  value: [200, 800],
  data1: [10, 100, 200, 250, 500, 750, 800, 1000],
});
const store = useProductsStore();
const { getCategory, getBrands, getColors } = storeToRefs(store);

const emit = defineEmits(['allFilters', 'priceVal']);
onMounted(() => {
  emit('priceVal', range.value);
});
function appliedFilter() {
  emit('allFilters', applyFilter.value);
}
</script>
