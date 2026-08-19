<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Touchspin with Postfix</h5>
        <span>Add <code>data-bts-postfix="POSTFIX_VALUE"</code> attribute to input to add postfix to touchspin input group.</span>
      </div>
      <div class="card-body">
        <fieldset>
          <div class="input-group">
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num3--"><i class="fa fa-minus"></i></button>
            <input class="touchspin form-control" type="text" v-model="num3" />
            <span class="input-group-text">%</span>
            <button type="button" class="btn btn-primary btn-square bootstrap-touchspin-down" @click="num3++"><i class="fa fa-plus"></i></button>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const num3 = ref<number>(40);
watch(num3, newValue => {
  if (newValue >= 100) {
    num3.value = 100;
  } else if (newValue <= 0) {
    num3.value = 0;
  }
});
</script>
