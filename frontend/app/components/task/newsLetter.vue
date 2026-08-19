<template>
  <div class="fade tab-pane" id="pills-newsletter" v-bind:class="activeclass === 'pills-newsletter' ? 'active show' : ''" role="tabpanel" aria-labelledby="pills-newsletter-tab">
    <div class="card mb-0">
      <div class="card-header d-flex">
        <h6 class="mb-0">Newsletter</h6>
        <a href="javascript:void(0)" @click="printWindow()"> <Icon name="clarity:printer-line" class="me-2" size="20" />Print </a>
      </div>
      <div class="card-body">
        <div class="details-bookmark text-center"><span>No tasks found.</span></div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const store = useProjectStore();
const { activeclass } = storeToRefs(store);
function printWindow() {
  window.print();
}
</script>
