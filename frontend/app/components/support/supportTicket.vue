<template>
  <div class="row">
    <div class="col-xl-4 col-sm-6" v-for="(item, index) in ticket" :key="index">
      <div class="card ecommerce-widget pro-gress">
        <div class="card-body support-ticket-font">
          <div class="row">
            <div class="col-5">
              <h6>{{ item.title }}</h6>
              <h4 class="total-num counter">
                <CommenNumberAnimations :data="item.number" />
              </h4>
            </div>
            <div class="col-7">
              <div class="text-md-end">
                <ul>
                  <li>
                    Profit<span class="product-stts txt-primary ms-2">8989<i class="icon-angle-up f-12"></i></span>
                  </li>
                  <li>
                    Loss<span class="product-stts txt-danger ms-2">2560<i class="icon-angle-down f-12"></i></span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          <div class="progress-showcase">
            <div class="progress">
              <div class="progress-bar" :class="item.progress" role="progressbar" style="width: 70%" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useSupportStore } from '~/store/support';

const store = useSupportStore();
const { ticket } = storeToRefs(store);
</script>
