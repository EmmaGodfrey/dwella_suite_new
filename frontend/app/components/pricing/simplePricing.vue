<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Simple Pricing Card</h5>
      </div>
      <div class="card-body pricing-content">
        <div class="row">
          <div class="col-xl-3 col-sm-6 xl-25 box-col-3" v-for="(item, index) in pricing" :key="index">
            <div class="card text-center pricing-simple">
              <div class="card-body">
                <h3>{{ item.title }}</h3>
                <h1>{{ item.price }}</h1>
                <h6 class="mb-0">{{ item.title }} Price</h6>
              </div>
              <a class="btn btn-lg btn-primary btn-block" href="javascript:void(0)">
                <h5 class="mb-0">Purchase</h5>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useInvoiceStore } from '~/store/invoice';

const store = useInvoiceStore();
const { simplePricing } = storeToRefs(store);
const pricing = simplePricing.value;
</script>
