<template>
  <div class="col-sm-12 col-xl-6" v-for="(element, index) in creative" :key="index">
    <div class="card" :class="element.card">
      <div class="card-header" :class="element.header">
        <h5 :class="element.class">{{ element.title }}</h5>
      </div>
      <div class="card-body">
        <p>{{ element.desc }}</p>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useCardStore } from '~/store/card';

const store = useCardStore();
const { creative } = storeToRefs(store);
</script>
