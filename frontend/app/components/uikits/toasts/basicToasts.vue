<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Toastr</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-success" type="button" @click="success" variant="success">Success</button>

        <button class="btn btn-info" type="button" @click="info" variant="info">Info</button>

        <button class="btn btn-danger" type="button" @click="error" variant="danger">Error</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

function success() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
function info() {
  toast.info(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
function error() {
  toast.error(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
</script>
