<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Pricing</h5>
      </div>
      <div class="card-body pricing-content">
        <div class="row pricing-col">
          <div class="col-xl-3 col-sm-6 xl-25 box-col-3" v-for="(item, index) in pricing" :key="index">
            <div class="pricing-block card text-center">
              <div class="pricing-header">
                <h2>{{ item.title }}</h2>
                <div class="price-box">
                  <div>
                    <h3>{{ item.price }}</h3>
                    <p>/ month</p>
                  </div>
                </div>
              </div>
              <div class="pricing-list">
                <ul class="pricing-inner">
                  <li>
                    <h6>{{ item.disk }}<span> Disk Space</span></h6>
                  </li>
                  <li>
                    <h6>{{ item.email }}<span> Email Accounts</span></h6>
                  </li>
                  <li>
                    <h6>{{ item.bandwidth }}<span> Bandwidth</span></h6>
                  </li>
                  <li>
                    <h6>{{ item.Sub }}<span> Subdomains</span></h6>
                  </li>
                  <li>
                    <h6>{{ item.domains }}<span> Domains</span></h6>
                  </li>
                </ul>
                <button class="btn btn-primary btn-lg" type="button" data-original-title="btn btn-primary btn-lg" title="">Subscribe</button>
              </div>
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
const { pricing } = storeToRefs(store);
</script>
