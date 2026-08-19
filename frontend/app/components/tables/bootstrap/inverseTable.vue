<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Inverse Table</h5>
        <span>Use a class <code>table-inverse</code> inside table element.</span>
      </div>
      <div class="table-responsive custom-scrollbar">
        <table class="table table-inverse">
          <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">First Name</th>
              <th scope="col">Last Name</th>
              <th scope="col">Office</th>
              <th scope="col">Position</th>
              <th scope="col">Salary</th>
              <th scope="col">Join Date</th>
              <th scope="col">Age</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(data, index) in bootstraplist" :key="index">
              <th scope="row">{{ data.id }}</th>
              <td>{{ data.firstName }}</td>
              <td>{{ data.lastName }}</td>
              <td>{{ data.office }}</td>
              <td>{{ data.role }}</td>
              <td>{{ data.salary }}</td>
              <td>{{ data.join }}</td>
              <td>{{ data.age }}</td>
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
const { inverse } = storeToRefs(store);
const bootstraplist = inverse.value;
</script>
