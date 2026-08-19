<template>
  <div class="col-sm-12 col-xl-6" v-for="(item, index) in basic" :key="index">
    <div class="card">
      <div class="card-header pb-0" v-html="item.title"></div>
      <div class="card-body">
        <p class="mb-0">{{ item.description }}</p>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6">
    <div class="card height-equal">
      <div class="card-header pb-0">
        <h5>Card With Footer</h5>
      </div>
      <div class="card-body">
        <p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the the industry's standard dummy text ever.</p>
      </div>
      <div class="card-footer">
        <h6 class="mb-0">Card Footer</h6>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6" v-for="(element, index) in footer" :key="index">
    <div class="card">
      <div class="card-header pb-0" :class="element.color">
        <h5 class="text-white">{{ element.title }}</h5>
      </div>
      <div class="card-body" :class="element.body">
        <p class="mb-0">{{ element.description }}</p>
      </div>
      <div class="card-footer" :class="element.body">
        <h6 class="mb-0">Card Footer</h6>
      </div>
    </div>
  </div>
  <div class="col-sm-12 col-xl-6" v-for="(element, index) in body" :key="index">
    <div class="card">
      <div class="card-header" :class="element.color">
        <h5 :class="element.class">{{ element.title }}</h5>
      </div>
      <div class="card-body" :class="element.body">
        <p class="mb-0">{{ element.description }}</p>
      </div>
      <div class="card-footer" :class="element.footer">
        <h6 class="mb-0">Card Footer</h6>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useCardStore } from '~/store/card';

const store = useCardStore();
const { basic, footer, cardbody } = storeToRefs(store);
const body = cardbody.value;
</script>
