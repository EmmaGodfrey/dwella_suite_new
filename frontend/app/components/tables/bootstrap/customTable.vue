<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Custom Table Color with Hover and Stripped</h5>
        <span
          >Use class<code>table-hover, table-striped table-*</code
          ><code>table-info</code
          >,<code>table-success</code>,<code>table-success</code>,<code>table-info</code>,<code>table-danger</code>,<code>table-primary</code>,<code>table-secondary</code>,<code>table-light</code>,<code
            >table-active</code
          >
          inside table element.</span
        >
      </div>
      <div class="card-block row">
        <div class="col-sm-12 col-lg-12 col-xl-12">
          <div class="table-responsive table-border-radius custom-scrollbar">
            <table class="table table-styling table-striped bg-info hover">
              <thead>
                <tr>
                  <th scope="col">Id</th>
                  <th scope="col">Film Title</th>
                  <th scope="col">Released</th>
                  <th scope="col">Studio</th>
                  <th scope="col">Budget</th>
                  <th scope="col">Domestic Gross</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(data, index) in bootstraplist" :key="index">
                  <th scope="row">{{ data.id }}</th>
                  <td>{{ data.film }}</td>
                  <td>{{ data.released }}</td>
                  <td>{{ data.studio }}</td>
                  <td>{{ data.budget }}</td>
                  <td>{{ data.domestic }}</td>
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
const { custom } = storeToRefs(store);
const bootstraplist = custom.value;
</script>
