<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Default Touchspin</h5>
        <span>Add <code>.touchspin</code> class to input to add touchspin input group.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num1--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num1" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num1++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num1 = ref<number>(40);
watch(num1, newValue => {
  if (newValue >= 100) {
    num1.value = 100;
  } else if (newValue <= 0) {
    num1.value = 0;
  }
});
</script>
