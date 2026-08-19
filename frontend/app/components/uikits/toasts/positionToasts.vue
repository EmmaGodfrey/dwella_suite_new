<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">toastr with position</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-primary" type="button" @click="topRight" variant="primary">Top Right</button>

        <button class="btn btn-primary" type="button" @click="topLeft" variant="primary">Top Left</button>

        <button class="btn btn-primary" type="button" @click="topCenter" variant="primary">Top Center</button>

        <button class="btn btn-primary" type="button" @click="bottomRight" variant="primary">Bottom Right</button>

        <button class="btn btn-primary" type="button" @click="bottomLeft" variant="primary">Bottom Left</button>

        <button class="btn btn-primary" type="button" @click="bottomCenter" variant="primary">Bottom Center</button>

        <button class="btn btn-primary" type="button" @click="fullWidth" variant="primary">Full Width</button>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';

function fullWidth() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
function topRight() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-right',
  });
}
function topLeft() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-left',
  });
}
function topCenter() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'top-center',
  });
}
function bottomRight() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'bottom-right',
  });
}
function bottomLeft() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'bottom-left',
  });
}
function bottomCenter() {
  toast.success(' New order has been placed ', {
    hideProgressBar: true,
    autoClose: 2000,
    theme: 'colored',
    position: 'bottom-center',
  });
}
</script>
