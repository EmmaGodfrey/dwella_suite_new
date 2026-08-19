<template>
  <div>
    <div class="table-responsive invoice-table custom-scrollbar" id="table">
      <table class="table table-bordered table-striped">
        <tbody>
          <tr>
            <td class="item">
              <h6 class="p-2 mb-0">Item Description</h6>
            </td>
            <td class="Hours">
              <h6 class="p-2 mb-0">Hours</h6>
            </td>
            <td class="Rate">
              <h6 class="p-2 mb-0">Rate</h6>
            </td>
            <td class="subtotal">
              <h6 class="p-2 mb-0">Sub-total</h6>
            </td>
          </tr>
          <tr v-for="(items, index) in invoice" :key="index">
            <td>
              <label>{{ items.title }}</label>
              <p class="m-0">{{ items.desc }}</p>
            </td>
            <td>
              <p class="itemtext digits mb-0">{{ items.hours }}</p>
            </td>
            <td>
              <p class="itemtext digits mb-0">$75</p>
            </td>
            <td>
              <p class="itemtext digits mb-0">{{ items.Subtotal }}</p>
            </td>
          </tr>
          <tr>
            <td>
              <p class="itemtext"></p>
            </td>
            <td>
              <p class="m-0">HST</p>
            </td>
            <td>
              <p class="m-0 digits">13%</p>
            </td>
            <td>
              <p class="m-0 digits">$419.25</p>
            </td>
          </tr>
          <tr>
            <td></td>
            <td></td>
            <td class="Rate">
              <h6 class="mb-0 p-2">Total</h6>
            </td>
            <td class="payment digits">
              <h6 class="mb-0 p-2">$3,644.25</h6>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="row mt-3">
      <div class="col-md-8">
        <div>
          <p class="legal">
            <strong>Thank you for your business!</strong> Payment is expected within 31 days; please process this invoice within that time. There will be a 5% interest charge per month on late
            invoices.
          </p>
        </div>
      </div>
      <div class="col-md-4"></div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useInvoiceStore } from '~/store/invoice';

const store = useInvoiceStore();
const { data } = storeToRefs(store);
const invoice = data.value;
</script>
