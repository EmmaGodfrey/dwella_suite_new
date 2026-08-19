<template>
  <div class="order-history table-responsive">
    <form>
      <div class="mb-3 row justify-content-end">
        <label for="table-complete-search" class="col-xs-3 col-sm-auto col-form-label">Search:</label>
        <div class="col-xs-3 col-sm-auto">
          <input id="table-complete-search" type="text" class="form-control" v-model="filterQuery" />
        </div>
      </div>
      <table class="table display border" id="basic-1">
        <thead>
          <tr>
            <th scope="col">Product</th>
            <th scope="col">Product name</th>
            <th scope="col">Size</th>
            <th scope="col">Color</th>
            <th scope="col">Article number</th>
            <th scope="col">Units</th>
            <th scope="col">Price</th>
            <th scope="col"><i class="fa fa-angle-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in getRows()" :key="index">
            <td>
              <nuxt-link to="/ecommerce/details/1"><img class="img-fluid img-30" :src="getImgUrl(row.images)" :alt="row.product1" /></nuxt-link>
            </td>
            <td>
              <div class="product-name">
                <a href="#">{{ row.product1 }}</a>
                <div class="order-process"><span class="order-process-circle" :class="getStatusClass(row.orderStatus)"></span>{{ row.orderStatus }}</div>
              </div>
            </td>
            <td>{{ row.size }}</td>
            <td>{{ row.color }}</td>
            <td>{{ row.articlenumber }}</td>
            <td>{{ row.units }}</td>
            <td>${{ row.price }}</td>
            <td>
              <Icon name="ci:more-vertical" class="" size="20" />
            </td>
          </tr>
        </tbody>
      </table>
      <ul class="pagination mt-2 justify-content-end pagination-primary">
        <li class="page-item">
          <a class="page-link" v-on:click="prev()" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>
        </li>
        <li class="page-item" v-for="i in numPages()" :key="i" v-bind:class="[i == currentPage ? 'active' : '']" v-on:click="changePage(i)">
          <a class="page-link">{{ i }}</a>
        </li>
        <li class="page-item">
          <a class="page-link" v-on:click="change()" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>
        </li>
      </ul>
    </form>
  </div>
</template>
<script lang="ts" setup>
import { useOrderhistoryStore } from '~/store/orderhistory';
import orderHistory from '~/types/orderHistory';

const elementsPerPage = ref<number>(10);
const currentPage = ref<number>(1);
const filterQuery = ref<string>('');
const allData = ref<orderHistory[]>([]);
const store = useOrderhistoryStore();
const { data } = storeToRefs(store);
const orderItems = data.value;

onMounted(() => {
  allData.value = orderItems;
});
watch(filterQuery, (search: string) => {
  var filteredData = orderItems.filter(row => {
    return row.product1.toLowerCase().includes(search.toLowerCase()) || row.size.toLowerCase().includes(search.toLowerCase()) || row.color.toLowerCase().includes(search.toLowerCase());
  });
  search == '' ? (allData.value = orderItems) : (allData.value = filteredData);
});
function getRows() {
  var start = (currentPage.value - 1) * elementsPerPage.value;
  var end = start + elementsPerPage.value;
  return allData.value.slice(start, end);
}
function getStatusClass(status: string) {
  if (status === 'shipped') {
    return 'shipped-order';
  } else if (status == 'processing') return '';
  else if (status === 'cancelled') return 'cancel-order';
  else return '';
}
function getImgUrl(path: string) {
  return '/images/' + path;
}
function numPages() {
  return Math.ceil(allData.value.length / elementsPerPage.value);
}
function changePage(page: number) {
  currentPage.value = page;
}
function change() {
  currentPage.value++;
}
function prev() {
  currentPage.value--;
}
</script>
