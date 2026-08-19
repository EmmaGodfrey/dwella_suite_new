<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Touchspin with initial Value</h5>
        <span>Add <code>data-bts-init-val="VALUE"</code> attribute attribute to set initial value for input group.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num6--"><i class="fa fa-minus"></i></button>

            <input class="touchspin form-control" type="text" v-model="num6" />

            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num6++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num6 = ref<number>(40);
watch(num6, newValue => {
  if (newValue >= 100) {
    num6.value = 100;
  } else if (newValue <= 0) {
    num6.value = 0;
  }
});
</script>
