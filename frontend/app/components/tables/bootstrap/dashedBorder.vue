<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Dashed Border</h5>
        <span> Dashed border use class <code>.table-dashed</code>, for Dotted border use class <code>.table-dotted</code>, for Double border use class <code>.table-Double</code></span>
      </div>
      <div class="table-responsive custom-scrollbar">
        <table class="table table-dashed">
          <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Classname</th>
              <th scope="col">Type</th>
              <th scope="col">Hours</th>
              <th scope="col">Trainer</th>
              <th scope="col">Spots</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in bootstraplist" :key="index">
              <th scope="row">{{ item.id }}</th>
              <td>{{ item.className }}</td>
              <td>{{ item.type }}</td>
              <td>{{ item.hours }}</td>
              <td>{{ item.trainer }}</td>
              <td>{{ item.spot }}</td>
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
const { dashed } = storeToRefs(store);
const bootstraplist = dashed.value;
</script>
