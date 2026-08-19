<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Basic Examples</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-primary sweet-1" type="button" v-on:click="basic">Basic</button>
        <button class="btn btn-primary sweet-2" type="button" v-on:click="basicWithTitle">With Title alert</button>
        <button class="btn btn-success sweet-3" type="button" v-on:click="basicSuccessAlert">Success alert</button>
        <button class="btn btn-info sweet-4" type="button" v-on:click="basicInfoAlert">Info alert</button>
        <button class="btn btn-warning sweet-5" type="button" v-on:click="basicWarningAlert">Warning alert</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

function basic() {
  swal.fire({
    confirmButtonColor: 'var(--theme-default)',
    title: 'Hello world!',
  });
}
function basicWarningAlert() {
  swal
    .fire({
      icon: 'warning',
      title: 'Are you sure?',
      text: 'Once deleted, you will not be able to recover this imaginary file!',
      showCancelButton: true,
      confirmButtonText: 'Ok',
      confirmButtonColor: 'var(--theme-default)',
      cancelButtonText: 'Cancel',
      cancelButtonColor: '#efefef',
    })
    .then(result => {
      if (result) {
        swal.fire({
          icon: 'success',
          text: 'Poof! Your imaginary file has been deleted!',
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({
          text: 'Your imaginary file is safe!',
          confirmButtonColor: 'var(--theme-default)',
        });
      }
    });
}
function basicWithTitle() {
  swal.fire({
    confirmButtonColor: 'var(--theme-default)',
    title: "Here's the title",
    text: "...and here's the text!",
  });
}
function basicSuccessAlert() {
  swal.fire({
    confirmButtonColor: 'var(--theme-default)',
    icon: 'warning',
    title: 'Good job!',
    text: 'You clicked the button!',
  });
}
function basicInfoAlert() {
  swal
    .fire({
      text: ' Click on either the button or outside the modal.',
      confirmButtonColor: 'var(--theme-default)',
    })
    .then(result => {
      if (result.value) {
        swal.fire({
          text: 'The returned value is:' + result.value,
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({
          confirmButtonColor: 'var(--theme-default)',
          text: 'The returned value is:' + result.value,
        });
      }
    });
}
</script>
