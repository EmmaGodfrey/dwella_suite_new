<template>
  <div class="col-xl-2 col-md-6 box-col-6 xl-50 proorder-lg-1">
    <div class="card">
      <div class="card-body">
        <div class="filter-block">
          <h4>Brand</h4>
          <ul>
            <li v-for="(item, index) in data" :key="index">
              <div class="form-check">
                <input class="form-check-input" :id="item.for" type="checkbox" value="" />
                <label class="form-check-label" :for="item.for">{{ item.title }}</label>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <div class="collection-filter-block">
          <ul class="pro-services">
            <li>
              <div class="d-flex">
                <Icon name="bi:truck" class="" size="40" />
                <div class="flex-grow-1">
                  <h5>Free Shipping</h5>
                  <p>Free Shipping World Wide</p>
                </div>
              </div>
            </li>
            <li>
              <div class="d-flex">
                <Icon name="ic:round-access-time" class="" size="50" />
                <div class="flex-grow-1">
                  <h5>24 X 7 Service</h5>
                  <p>Online Service For New Customer</p>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

const store = useProductsStore();
const { block } = storeToRefs(store);
const data = block.value;
</script>
