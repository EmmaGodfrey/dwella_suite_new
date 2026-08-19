<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>outline buttons</h5>
      <span>Add <code>.btn-pill</code> and <code>.btn-outline-*</code> class for button with outline</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>bold Border outline buttons</h5>
      <span>Add <code>.btn-pill</code> and <code>.btn-outline-*-2x</code> class for button with bold outline</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill" :class="item.classes" v-for="(item, index) in data1" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>outline Large buttons</h5>
      <span>Add <code>.btn-pill</code>,<code>.btn-outline-*</code> and <code>.btn-lg</code> class for large button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill btn-lg" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>outline small buttons</h5>
      <span>Add <code>.btn-pill</code>,<code>.btn-outline-*</code> and <code>.btn-sm</code> class for small button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill btn-sm" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Outline extra small buttons</h5>
      <span>Add <code>.btn-pill</code>,<code>.btn-outline-*</code> and <code>.btn-xs</code> class for extra small button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-pill btn-xs" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Disabled outline buttons</h5>
      <span>Add <code>.disabled</code> class or <code>disabled="disabled"</code> attribute for disabled button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill disabled" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Disabled</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Gradien buttons</h5>
      <span>Add <code>.btn-pill</code> and <code>.btn-*-gradien</code>class for gradien button</span>
    </div>

    <div class="card-body btn-showcase">
      <button class="btn btn-pill" :class="item.classes" v-for="(item, index) in data2" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useCommenStore } from '~/store/commen';

const store = useCommenStore();
const { color, outline, gradien } = storeToRefs(store);
const data = color.value;
const data1 = outline.value;
const data2 = gradien.value;
</script>
