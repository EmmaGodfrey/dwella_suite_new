<template>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in ribbon" :key="index">
      <div class="ribbon-wrapper card">
        <div class="card-body">
          <div class="ribbon" :class="item.class">Ribbon</div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in vertical" :key="index">
      <div class="card" :class="item.card">
        <div class="card-body">
          <div class="ribbon" :class="item.class"><i :class="item.icon"></i></div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in bookmark" :key="index">
      <div class="ribbon-wrapper card">
        <div class="card-body">
          <div class="ribbon" :class="item.class">Ribbon</div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in verticalRight" :key="index">
      <div class="card" :class="item.card">
        <div class="card-body">
          <div class="ribbon" :class="item.class"><i :class="item.icon"></i></div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in clip" :key="index">
      <div class="ribbon-wrapper card">
        <div class="card-body">
          <div class="ribbon" :class="item.class">Ribbon</div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
  <div class="row">
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in clipRight" :key="index">
      <div class="ribbon-wrapper-bottom card">
        <div class="card-body">
          <div class="ribbon" :class="item.class">Ribbon</div>
          <p>{{ item.lorn }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useRibbonStore } from '~/store/ribbon';

const store = useRibbonStore();
const { right, verticalLeft, bookmark, verticalRight, clip, item } = storeToRefs(store);
const ribbon = right.value;
const vertical = verticalLeft.value;
const clipRight = item.value;
</script>
