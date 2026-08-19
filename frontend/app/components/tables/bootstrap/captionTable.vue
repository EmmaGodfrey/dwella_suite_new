<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Caption</h5>
        <span
          >A <code>&lt;caption&gt;</code> functions like a heading for a table. It helps users with screen readers to find a table and understand what it’s about and decide if they want to read
          it.</span
        >
      </div>
      <div class="card-block row">
        <div class="col-sm-12 col-lg-12 col-xl-12">
          <div class="table-responsive custom-scrollbar">
            <table class="table">
              <caption>
                List of users
              </caption>
              <thead>
                <tr>
                  <th scope="col">Id</th>
                  <th scope="col">Employee Name</th>
                  <th scope="col">Email</th>
                  <th scope="col">Experience</th>
                  <th scope="col">Sex</th>
                  <th scope="col">Contact No.</th>
                  <th scope="col">Age</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in bootstraplist" :key="index">
                  <th scope="row">{{ item.id }}</th>
                  <td>{{ item.name }}</td>
                  <td>{{ item.email }}</td>
                  <td>{{ item.exp }}</td>
                  <td>{{ item.sex }}</td>
                  <td>{{ item.contact }}</td>
                  <td>{{ item.age }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useBootstrapStore } from '~/store/bootstrap';

const store = useBootstrapStore();
const { caption } = storeToRefs(store);
const bootstraplist = caption.value;
</script>
