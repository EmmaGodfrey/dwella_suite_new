<template>
  <div class="card" id="custom-state-button">
    <div class="card-header pb-0">
      <h5>Custom state buttons</h5>
      <span>The <code>.btn</code> class used with <code>&lt;button&gt;</code>, <code>&lt;a&gt;</code> and <code>&lt;input&gt;</code> elements.</span>
    </div>
    <div class="card-body btn-showcase">
      <a class="btn btn-primary" href="javascript:void(0)" title="btn btn-primary" role="button">Link</a>
      <input class="btn btn-secondary" type="button" value="Input" title="btn btn-secondary" />
      <input class="btn btn-success" type="submit" value="Submit" title="btn btn-success" />
      <button class="btn btn-info" type="submit">Button</button>
    </div>
  </div>
  <div class="card" id="outline-button">
    <div class="card-header pb-0">
      <h5>outline buttons</h5>
      <span>Add <code>.btn-outline-*</code> class for border button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card" id="outline-bold-button">
    <div class="card-header pb-0">
      <h5>bold Border outline buttons</h5>
      <span>Add <code>.btn-outline-*-2x</code> class for bold outline</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn" :class="item.classes" v-for="(item, index) in data1" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card" id="outline-large-button">
    <div class="card-header pb-0">
      <h5>outline Large buttons</h5>
      <span>Add <code>.btn-outline-*</code> class for outline and <code>.btn-lg</code> class for large button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-lg" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card" id="outline-small-button">
    <div class="card-header pb-0">
      <h5>outline small buttons</h5>
      <span>Add <code>.btn-outline-*</code> class for outline and <code>.btn-sm</code> class for small button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-sm" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card" id="ex-outline-small-button">
    <div class="card-header pb-0">
      <h5>Outline extra small buttons</h5>
      <span>Add <code>.btn-outline-*</code> class for outline and <code>.btn-xs</code> class for extra small button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn btn-xs" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">{{ item.title }}</button>
    </div>
  </div>
  <div class="card">
    <div class="card-header pb-0">
      <h5>Disabled outline buttons</h5>
      <span>Add <code>.disabled</code> class or <code>disabled="disabled"</code> attribute for disabled state</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn disabled" :class="item.classes" v-for="(item, index) in data" :key="index" type="button">Disabled</button>
    </div>
  </div>
  <div class="card" id="gradiant">
    <div class="card-header pb-0">
      <h5>Gradien buttons</h5>
      <span>Add <code>.btn-*-gradien</code> class for gradien button</span>
    </div>
    <div class="card-body btn-showcase">
      <button class="btn" :class="item.classes" v-for="(item, index) in data2" :key="index" type="button">{{ item.title }}</button>
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
