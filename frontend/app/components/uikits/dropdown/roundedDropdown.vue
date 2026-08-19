<template>
  <div class="col-sm-12 col-xl-12">
    <div class="card card-overflow">
      <div class="card-header pb-0">
        <h5>Rounded Dropdown</h5>
      </div>
      <div class="card-body dropdown-basic">
        <div class="dropdown" v-for="(item, index) in data" :key="index">
          <div class="btn-group mb-0">
            <button class="dropbtn btn-round" :class="item.classes" type="button">
              {{ item.title }}<span><i class="icofont icofont-arrow-down"></i></span>
            </button>
            <div class="dropdown-content">
              <a href="#">Action</a>
              <a href="#">Another Action</a>
              <a href="#">Something Else Here</a>
              <a href="#">Separated Link </a>
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
