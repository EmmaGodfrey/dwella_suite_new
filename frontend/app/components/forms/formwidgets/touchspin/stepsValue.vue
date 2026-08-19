<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Touchspin steps</h5>
        <span>Add <code>data-bts-step="VALUE"</code> attribute for increament and decrement steps to touchspin input group.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num7--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num7" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num7++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num7 = ref<number>(40);
watch(num7, newValue => {
  if (newValue >= 100) {
    num7.value = 100;
  } else if (newValue <= 0) {
    num7.value = 0;
  }
});
</script>
