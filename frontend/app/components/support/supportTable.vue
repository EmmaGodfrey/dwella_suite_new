<template>
  <div class="table-responsive support-table data-table">
    <form>
      <div class="mb-3 row justify-content-end">
        <label for="table-complete-search" class="col-xs-3 col-sm-auto col-form-label">Search:</label>
        <div class="col-xs-3 col-sm-auto">
          <input id="table-complete-search" type="text" class="form-control" name="searchTerm" v-model="filterQuery" />
        </div>
      </div>
      <table class="table table-striped table-bordered" id="basic-6">
        <thead>
          <tr>
            <th scope="col" sortable="name">Name</th>
            <th scope="col" sortable="position">Position</th>
            <th scope="col" sortable="salary">Salary</th>
            <th scope="col" sortable="office">Office</th>
            <th scope="col" sortable="skill">Skill</th>
            <th scope="col" sortable="extn">Extend</th>
            <th scope="col" sortable="email">Email</th>
            <th scope="col" sortable="exp">Experience</th>
            <th scope="col">Action</th>
          </tr>
        </thead>
        <tbody v-if="!getRows().length">
          <tr class="odd">
            <td valign="top" colspan="6" class="dataTables_empty">No matching records found</td>
          </tr>
        </tbody>
        <tbody v-if="getRows().length">
          <tr v-for="(row, index) in getRows()" :key="index">
            <td>
              <div class="d-flex">
                <img class="rounded-circle img-30 me-3" :src="getImages(row.img)" alt="Generic placeholder image" />
                <div class="flex-grow-1 align-self-center">
                  <div>{{ row.name }}</div>
                </div>
              </div>
            </td>
            <td>{{ row.position }}</td>
            <td>{{ row.salary }}</td>
            <td>{{ row.office }}</td>
            <td>
              <div class="progress-showcase">
                <div class="progress sm-progress-bar">
                  <div class="progress-bar" :class="row.skill" role="progressbar" :style="{ width: row.progress }" aria-valuenow="50" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
              </div>
            </td>
            <td>{{ row.extn }}</td>
            <td>{{ row.email }}</td>
            <td>{{ row.exp }}</td>
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
      <ul class="pagination mt-2 justify-content-end">
        <li class="page-item"><a class="page-link" @click="prev()">Previous</a></li>
        <li class="page-item" v-for="i in numPages()" :key="i" v-bind:class="[i == currentPage ? 'active' : '']" v-on:click="changePage(i)">
          <a class="page-link">{{ i }}</a>
        </li>
        <li class="page-item"><a class="page-link" @click="change()">Next</a></li>
      </ul>
    </form>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useSupportStore } from '~/store/support';
import table from '~/types/supportDetails';

const elementsPerPage = ref<number>(10);
const currentPage = ref<number>(1);
const filterQuery = ref<string>('');
const allData = ref<table[]>([]);
const store = useSupportStore();
const { item } = storeToRefs(store);
const orderItems = item.value;
onMounted(() => {
  allData.value = orderItems;
});
watch(filterQuery, (search: string) => {
  var filteredData = orderItems.filter(row => {
    return (
      row.name.toLowerCase().includes(search.toLowerCase()) ||
      row.position.toLowerCase().includes(search.toLowerCase()) ||
      row.office.toLowerCase().includes(search.toLowerCase()) ||
      row.salary.toLowerCase().includes(search.toLowerCase())
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
  currentPage.value--;
}
function removeProduct(index: number) {
  orderItems.splice(index, 1);
}
</script>
