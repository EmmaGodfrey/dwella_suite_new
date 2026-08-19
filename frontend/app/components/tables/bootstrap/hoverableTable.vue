<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>Hoverable rows with Horizontal Border</h5>
        <span
          >Hoverable row use a class <code>table-hover</code> and for Horizontal border use a class <code>.table-border-horizontal</code> , Solid border Use a class <code>.border-solid</code>
          <code>.table</code> class.</span
        >
      </div>
      <div class="table-responsive custom-scrollbar">
        <table class="table table-hover">
          <thead>
            <tr>
              <th scope="col">Id</th>
              <th scope="col">Status</th>
              <th scope="col">Signal Name</th>
              <th scope="col">Security</th>
              <th scope="col">Stage</th>
              <th scope="col">Schedule</th>
              <th scope="col">Team Lead</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(data, index) in bootstraplist" :key="index">
              <th scope="row">{{ data.id }}</th>
              <td :Class="data.status" class="d-flex align-items-center">
                <span :class="`icon-box bg-light-${data.bgClass}`">
                  <Icon :name="data.icon" :class="`font-${data.bgClass}`" class="" size="20" />
                </span>
                <span :class="[data.font, 'ms-2']">{{ data.status }}</span>
              </td>
              <td>{{ data.signalName }}</td>
              <td>{{ data.security }}</td>
              <td>{{ data.stage }}</td>
              <td>{{ data.schedule }}</td>
              <td>{{ data.teamLead }}</td>
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
const { hoverable } = storeToRefs(store);
const bootstraplist = hoverable.value;
</script>
