<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Sizing Tables</h5>
        <span
          >Example of Extra large table, Add <code>.table-xl</code> class to the <code>.table</code> , Large table Add <code>.table-lg</code> , Default table Add <code>.table-de</code> , Small table
          Add <code>.table-sm </code> , Extra Small table Add <code>.table-xs</code> to create a table. "</span
        >
      </div>
      <div class="table-responsive custom-scrollbar">
        <table class="table table-lg">
          <thead>
            <tr>
              <th>Id</th>
              <th>Employee Name</th>
              <th>Date</th>
              <th>Status</th>
              <th>Hours</th>
              <th>Performance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in bootstrapList" :key="index">
              <th scope="row">{{ item.id }}</th>
              <td>{{ item.Name }}</td>
              <td>{{ item.Date }}</td>
              <td :class="item.statusClass">{{ item.Status }}</td>
              <td>{{ item.hours }}</td>
              <td>{{ item.performance }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useBootstrapStore } from '~/store/bootstrap';

const store = useBootstrapStore();
const { sizing } = storeToRefs(store);
const bootstrapList = sizing.value;
</script>
