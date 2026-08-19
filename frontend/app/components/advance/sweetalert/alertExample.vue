<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Alert State</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-success sweet-8" type="button" v-on:click="successAlertState">Success</button>
        <button class="btn btn-danger sweet-7" type="button" v-on:click="dangerAlertState">Danger</button>
        <button class="btn btn-info sweet-9" type="button" v-on:click="infoAlertState">Information</button>
        <button class="btn btn-warning sweet-6" type="button" v-on:click="warningAlertState">Warning</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

function successAlertState() {
  swal.fire({
    icon: 'success',
    title: 'Good job!',
    text: 'You clicked the button!',
    confirmButtonColor: 'var(--theme-default)',
  });
}
function dangerAlertState() {
  swal.fire({
    icon: 'error',
    title: 'Good job!',
    text: 'You clicked the button!',
    confirmButtonColor: 'var(--theme-default)',
  });
}
function infoAlertState() {
  swal.fire({
    icon: 'info',
    title: 'Good job!',
    text: 'You clicked the button!',
    confirmButtonColor: 'var(--theme-default)',
  });
}
function warningAlertState() {
  swal.fire({
    icon: 'warning',
    title: 'Good job!',
    text: 'You clicked the button!',
    confirmButtonColor: 'var(--theme-default)',
  });
}
</script>
