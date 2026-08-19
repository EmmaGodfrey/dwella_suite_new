<template>
  <div class="col-xl-12 recent-order-sec">
    <div class="card">
      <div class="card-body">
        <div class="table-responsive">
          <h5>Recent Orders</h5>
          <table class="table table-bordernone">
            <thead>
              <tr>
                <th>Name</th>
                <th>Date</th>
                <th>Quantity</th>
                <th>Value</th>
                <th>Rate</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in data" :key="index">
                <td>
                  <div class="media">
                    <img class="img-fluid rounded-circle" :src="item.img" alt="" data-original-title="" title="" />
                    <div class="media-body">
                      <nuxt-link to="/ecommerce/product"
                        ><span>{{ item.title }}</span></nuxt-link
                      >
                    </div>
                  </div>
                </td>
                <td>
                  <p>{{ item.date }}</p>
                </td>
                <td>
                  <p>{{ item.quantity }}</p>
                </td>
                <td>
                  <img class="img-fluid" :src="item.value" alt="" data-orheader.notificationginal-title="" title="" />
                </td>
                <td>
                  <p>{{ item.rate }}</p>
                </td>
                <td>
                  <p>Done</p>
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
import { useDashboardStore } from '~/store/dashboard';

const store = useDashboardStore();
const { data } = storeToRefs(store);
</script>
