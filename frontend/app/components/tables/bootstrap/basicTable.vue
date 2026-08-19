<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Basic Table with Border Bottom Color</h5>
        <span>Use a class<code>.table</code> to any table, and <code>.border-bottom-*</code> class for Border bottom color</span>
      </div>
      <div class="table-responsive custom-scrollbar">
        <table class="table">
          <thead>
            <tr class="border-bottom-primary">
              <th scope="col">Id</th>
              <th scope="col">First Name</th>
              <th scope="col">Last Name</th>
              <th scope="col">Username</th>
              <th scope="col">Designation</th>
              <th scope="col">Company</th>
              <th scope="col">Language</th>
              <th scope="col">Country</th>
            </tr>
          </thead>
          <tbody>
            <tr :class="data.borderColor" v-for="(data, index) in bootstraplist" :key="index">
              <th scope="row">{{ data.id }}</th>
              <td><img :src="getImages(data.img)" alt="" class="img-30 me-2 rounded-circle" />{{ data.firstName }}</td>
              <td>{{ data.lastName }}</td>
              <td>{{ data.userName }}</td>
              <td>{{ data.role }}</td>
              <td>{{ data.company }}</td>
              <td>
                <div class="badge" :class="data.badgeClass">
                  {{ data.language }}
                </div>
              </td>
              <td>{{ data.country }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useBootstrapStore } from '~/store/bootstrap';

const store = useBootstrapStore();
const { data } = storeToRefs(store);
const bootstraplist = data.value;
</script>
