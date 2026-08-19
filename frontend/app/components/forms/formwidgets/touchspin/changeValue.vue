<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Change Button Class to link</h5>
        <span>Add <code>data-bts-button-down-class & data-bts-button-up-class</code> attribute to change button Class.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num8--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num8" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num8++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num8 = ref<number>(50);
watch(num8, newValue => {
  if (newValue >= 100) {
    num8.value = 100;
  } else if (newValue <= 0) {
    num8.value = 0;
  }
});
</script>
