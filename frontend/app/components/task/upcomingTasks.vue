<template>
  <div class="fade tab-pane" id="pills-upcoming" v-bind:class="activeclass === 'pills-upcoming' ? 'active show' : ''" role="tabpanel" aria-labelledby="pills-upcoming-tab">
    <div class="card mb-0">
      <div class="card-header d-flex">
        <h6 class="mb-0">Upcoming Tasks</h6>
        <a href="javascript:void(0)" @click="printWindow()"> <Icon name="clarity:printer-line" class="me-2" size="20" />Print </a>
      </div>
      <div class="card-body">
        <div class="details-bookmark text-center">
          <div class="row" id="favouriteData"></div>
          <div class="no-favourite"><span>No task due today.</span></div>
        </div>
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
