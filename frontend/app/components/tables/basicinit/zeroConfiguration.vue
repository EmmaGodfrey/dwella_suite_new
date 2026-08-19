<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h4>Zero Configuration</h4>
        <span>DataTables has most features enabled by default, so all you need to do to use it with your own tables is to call the construction function:<code>$().DataTable();</code>.</span
        ><span>Searching, ordering and paging goodness will be immediately added to the table, as shown in this example.</span>
      </div>
      <div class="card-body">
        <div class="table-responsive data-table custom-scrollbar zero-configuration">
          <form>
            <div class="mb-3 row justify-content-end">
              <label for="table-complete-search" class="col-xs-3 col-sm-auto col-form-label">Search:</label>
              <div class="col-xs-3 col-sm-auto">
                <input id="table-complete-search" type="text" class="form-control" v-model="filterQuery" />
              </div>
            </div>
            <table class="table table-striped table-bordered">
              <thead>
                <tr>
                  <th scope="col" sortable="name">Name</th>
                  <th scope="col" sortable="startDate">Date</th>
                  <th scope="col" sortable="invoice">Invoice No.</th>
                  <th scope="col" sortable="position">Job Designation</th>
                  <th scope="col" sortable="credit">Credit/Debit</th>
                  <th scope="col" sortable="office">Company Name</th>
                  <th scope="col" sortable="salary">Priority</th>
                  <th scope="col" sortable="Budget">Budget</th>
                  <th scope="col">Action</th>
                </tr>
              </thead>
              <tbody v-if="!getRows().length">
                <tr class="odd">
                  <td valign="top" colspan="7" class="dataTables_empty">No matching records found</td>
                </tr>
              </tbody>
              <tbody v-if="getRows().length">
                <tr v-for="(row, index) in getRows()" :key="index">
                  <td scope="row"><img class="img-40 me-2" :src="getImages(row.img)" alt="" />{{ row.name }}</td>
                  <td>{{ row.startDate }}</td>
                  <td>{{ row.invoice }}</td>
                  <td>{{ row.position }}</td>
                  <td>
                    <span class="f-w-700" :class="row.iconColor">
                      <i class="icofont" :class="row.iconClass"></i>
                      {{ row.credit }}
                    </span>
                  </td>
                  <td>{{ row.office }}</td>
                  <td>
                    <span class="badge" :class="row.ActionClass">{{ row.salary }}</span>
                  </td>
                  <td>{{ row.Budget }}</td>
                  <td>
                    <span>
                      <span @click="removeProduct(index)">
                        <i class="icofont icofont-close-circled font-danger ps-2"></i>
                      </span>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
            <ul class="pagination mt-2 justify-content-end pagination-primary">
              <li class="page-item">
                <a class="page-link" @click="prev()" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>
              </li>
              <li class="page-item" v-for="i in numPages()" :key="i" v-bind:class="[i == currentPage ? 'active' : '']" v-on:click="changePage(i)">
                <a class="page-link">{{ i }}</a>
              </li>
              <li class="page-item">
                <a class="page-link" @click="change()" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>
              </li>
            </ul>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useDatatableStore } from '~/store/datatable';
import table from '~/types/datatable';

const elementsPerPage = ref<number>(6);
const currentPage = ref<number>(1);
const filterQuery = ref<string>('');
const allData = ref<table[]>([]);
const store = useDatatableStore();
const { data } = storeToRefs(store);
const orderItems = data.value;
onMounted(() => {
  allData.value = orderItems;
});
watch(filterQuery, (search: string) => {
  var filteredData = orderItems.filter(row => {
    return (
      row.name.toLowerCase().includes(search.toLowerCase()) ||
      row.position.toLowerCase().includes(search.toLowerCase()) ||
      row.office.toLowerCase().includes(search.toLowerCase()) ||
      row.salary.toLowerCase().includes(search.toLowerCase()) ||
      row.Budget.toLowerCase().includes(search.toLowerCase())
    );
  });
  search == '' ? (allData.value = orderItems) : (allData.value = filteredData);
});
function getRows() {
  var start = (currentPage.value - 1) * elementsPerPage.value;
  var end = start + elementsPerPage.value;
  return allData.value.slice(start, end);
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
  if (currentPage.value > 1) {
    currentPage.value--;
  }
}
function removeProduct(index: number) {
  orderItems.splice(index, 1);
}
</script>
