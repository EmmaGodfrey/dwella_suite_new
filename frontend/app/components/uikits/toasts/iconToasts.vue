<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">toastr with icon</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-success" type="button" @click="successWithIcon" variant="success">Success</button>

        <button class="btn btn-info" type="button" @click="infoWithIcon" variant="info">Info</button>

        <button class="btn btn-danger" type="button" @click="errorWithIcon" variant="danger">Error</button>

        <button class="btn btn-info" type="button" @click="infoWithCancle" variant="info">Cancle</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

function successWithIcon() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
  });
}
function infoWithIcon() {
  toast.info(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
  });
}
function errorWithIcon() {
  toast.error(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
  });
}
function infoWithCancle() {
  toast.info(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
  });
}
</script>
