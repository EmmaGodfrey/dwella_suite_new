<template>
  <form class="theme-form form-label-align-right range-slider">
    <div class="form-group mt-3 me-1 row">
      <label class="col-md-2 col-form-label sm-left-text" for="u-range-01">Default</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="one.value" :data="one.data" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-02">Min-Max Value</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="two.value" :data="two.data" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-03">Prefix</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="three.value" :data="three.data1" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-04">Nagative value</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="four.value" :data="four.data2" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-05">Steps</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="seven.value" :data="seven.data3" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-06">Custom Values</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="five.value" :data="five.data" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
    <div class="form-group mt-5 me-1 row">
      <label class="col-md-2 control-label sm-left-text" for="u-range-07">Prettify Numbers</label>
      <div class="col-md-10">
        <client-only> <VueSlider v-model="six.value" :data="six.data" :marks="true" :tooltip="'always'" :tooltip-placement="'top'"></VueSlider></client-only>
      </div>
    </div>
  </form>
</template>
<script lang="ts" setup>
import type rangFive from '~/types/rangFive';
import type rangFour from '~/types/rangFour';
import type rangSeven from '~/types/rangSeven';

interface rang {
  value: number;
  data: number[];
}
interface rangs {
  value: number[];
  data1: number[];
}
const one = ref<rang>({
  value: 10,
  data: [10, 100],
});
const two = ref<rang>({
  value: 550,
  data: [10, 100, 200, 250, 500, 550, 750, 800, 1000],
});
const three = ref<rangs>({
  value: [200, 800],
  data1: [10, 100, 200, 250, 500, 750, 800, 1000],
});
const four = ref<rangFour>({
  value: [-500, 500],
  data2: [-1000, -720, -500, -250, 0, 250, 500, 720, 1000],
});
const seven = ref<rangSeven>({
  value: [-500, 500],
  data3: [-1000, -720, -500, -250, 0, 250, 500, 720, 1000],
});
const five = ref<rangFive>({
  value: 'April',
  data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'],
});
const six = ref<rang>({
  value: 2000,
  data: [1000, 2000, 3250, 5500, 7750, 10000],
});
</script>
