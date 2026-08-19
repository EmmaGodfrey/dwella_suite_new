<template>
  <div class="col-sm-12 col-xl-12">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Dropdown Split Button</h5>
      </div>
      <div class="card-body dropdown-basic">
        <div class="btn-group" v-for="(item, index) in data" :key="index">
          <button class="btn" :class="item.classes" type="button">{{ item.title }}</button>
          <div class="dropdown separated-btn">
            <button class="btn" :class="item.classes" type="button"><i class="icofont icofont-arrow-down"></i></button>
            <div class="dropdown-content">
              <a href="#">Link 1</a>
              <a href="#">Link 2</a>
              <a href="#">Link 3</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useUikitStore } from '~/store/uikit';

const store = useUikitStore();
const { dropdown1 } = storeToRefs(store);
const data = dropdown1.value;
</script>
