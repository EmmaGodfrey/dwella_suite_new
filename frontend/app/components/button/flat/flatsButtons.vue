<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Default buttons</h5>
      <span>Add <code>.btn-square</code> class for flat button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Large buttons</h5>
      <span>Add <code>.btn-square</code> and <code>.btn-lg</code> class for large button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square btn-lg" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Small buttons</h5>
      <span>Add <code>.btn-square</code> and <code>.btn-sm</code> class for small button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square btn-sm" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Extra Small buttons</h5>
      <span>Add <code>.btn-square</code> and <code>.btn-xs</code> class for extra small button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square btn-xs" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Active Buttons</h5>
      <span>Add <code>.active</code> for active state</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square active" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Active</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Disabled buttons</h5>
      <span>Add <code>.disabled</code> class or <code>disabled="disabled"</code> attribute for disabled button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-square disabled" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Disabled</button>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useCommenStore } from '~/store/commen';

const store = useCommenStore();
const { data } = storeToRefs(store);
</script>
