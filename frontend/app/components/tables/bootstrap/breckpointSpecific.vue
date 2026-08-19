<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Breckpoint Specific</h5>
        <span
          >Use <code>.table-responsive{-sm|-md|-lg|-xl}</code> functions like a heading for a table. It helps users with screen readers to find a table and understand what it’s about and decide if
          they want to read it.</span
        >
      </div>
      <div class="card-block row">
        <div class="col-sm-12 col-lg-12 col-xl-12">
          <div class="table-responsive custom-scrollbar">
            <table class="table table-responsive-sm">
              <thead>
                <tr>
                  <th scope="col">Id</th>
                  <th scope="col">Name</th>
                  <th scope="col">Order Id</th>
                  <th scope="col">Price</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in bootstraplist" :key="index">
                  <th scope="row">{{ item.id }}</th>
                  <td>{{ item.name }}</td>
                  <td>{{ item.order }}</td>
                  <td>{{ item.price }}</td>
                  <td>{{ item.quantity }}</td>
                  <td>{{ item.total }}</td>
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
const { breckpoint } = storeToRefs(store);
const bootstraplist = breckpoint.value;
</script>
