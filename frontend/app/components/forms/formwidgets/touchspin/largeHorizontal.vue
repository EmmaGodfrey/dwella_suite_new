<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Large Horizontal Touchspin</h5>
      </div>
      <div class="card-body">
        <p>Add <code>.input-group-lg</code> class to input-group.</p>
        <fieldset>
          <div class="input-group input-group-lg">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num5--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num5" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num5++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num5 = ref<number>(40);
watch(num5, newValue => {
  if (newValue >= 100) {
    num5.value = 100;
  } else if (newValue <= 0) {
    num5.value = 0;
  }
});
</script>
