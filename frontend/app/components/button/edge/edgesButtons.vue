<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Default buttons</h5>
      <span>Add <code>.btn-pill</code> class for edge button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-pill" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Large buttons</h5>
      <span>Add <code>.btn-pill</code> and <code>.btn-lg</code> class for large button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill btn-lg" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Small buttons</h5>
      <span>Add <code>.btn-pill</code> and <code>.btn-sm</code> class for small button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill btn-sm" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Active Buttons</h5>
      <span>Add <code>.active</code> for active state</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill active" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Active</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Disabled buttons</h5>
      <span>Add <code>.disabled</code> class or <code>disabled="disabled"</code> attribute for disabled button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill disabled" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Disabled</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Custom state buttons</h5>
      <span>The <code>.btn</code> class used with <code>&lt;button&gt;</code>, <code>&lt;a&gt;</code> and <code>&lt;input&gt;</code> elements.</span>
    </div>
    <div class="card-body btn-showcase">
      <a class="btn btn-pill btn-primary" href="javascript:void(0)" data-bs-toggle="tooltip" title="btn btn-primary" role="button">Link</a>
      <input class="btn btn-pill btn-secondary" type="button" value="Input" data-bs-toggle="tooltip" title="btn btn-secondary" />
      <input class="btn btn-pill btn-success" type="submit" value="Submit" data-bs-toggle="tooltip" title="btn btn-success" />
      <button class="btn btn-pill btn-info" type="submit">Button</button>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useCommenStore } from '~/store/commen';

const store = useCommenStore();
const { data } = storeToRefs(store);
</script>
