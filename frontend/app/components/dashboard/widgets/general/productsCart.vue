<template>
  <div class="col-xl-6 xl-100 box-col-12">
    <div class="card">
      <div class="card-header pb-0 d-flex justify-content-between align-items-center">
        <h5>PRODUCTS CART</h5>
      </div>
      <div class="card-body">
        <div class="user-status table-responsive">
          <table class="table table-bordernone">
            <thead>
              <tr>
                <th scope="col">Details</th>
                <th scope="col">Quantity</th>
                <th scope="col">Status</th>
                <th scope="col">Price</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in data" :key="index">
                <td class="f-w-600 simply">{{ item.details }}</td>
                <td>{{ item.quantity }}</td>
                <td :class="item.font">{{ item.status }}</td>
                <td>
                  <div class="span badge rounded-pill" :class="item.class">{{ item.price }}</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useWidgetsStore } from '~/store/widgets';

const store = useWidgetsStore();
const { product } = storeToRefs(store);
const data = product.value;
</script>
