<template>
  <div class="col-xl-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Pagination alignment</h5>
      </div>
      <div class="card-body pagination-lastitems">
        <nav class="m-b-30" aria-label="Page navigation example" v-for="(item, index) in alignment" :key="index">
          <ul class="pagination" :class="item.class">
            <li class="page-item"><a class="page-link" href="javascript:void(0)">Previous</a></li>
            <li class="page-item"><a class="page-link" href="javascript:void(0)">1</a></li>
            <li class="page-item"><a class="page-link" href="javascript:void(0)">2</a></li>
            <li class="page-item"><a class="page-link" href="javascript:void(0)">3</a></li>
            <li class="page-item"><a class="page-link" href="javascript:void(0)">Next</a></li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { usePaginationStore } from '~/store/pagination';

const store = usePaginationStore();
const { alignment } = storeToRefs(store);
</script>
