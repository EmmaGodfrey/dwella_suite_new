<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Touchspin mousewheel Disable</h5>
        <span>Add <code>.touchspin-stop-mousewheel</code> class to diable mousewheel.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num5--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num5" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num5++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>

  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Small Horizontal Touchspin</h5>
        <span>Add <code>.input-group-sm</code> class to input-group.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num9--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num9" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num9++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num9 = ref<number>(60);
const num5 = ref<number>(40);
watch(num9, newValue => {
  if (newValue >= 100) {
    num9.value = 100;
  } else if (newValue <= 0) {
    num9.value = 0;
  }
});
watch(num5, newValue => {
  if (newValue >= 100) {
    num5.value = 100;
  } else if (newValue <= 0) {
    num5.value = 0;
  }
});
</script>
