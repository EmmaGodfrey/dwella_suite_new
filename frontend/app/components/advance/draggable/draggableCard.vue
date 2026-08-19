<template>
  <ClientOnly>
    <VueDraggableNext class="row">
      <div class="col-sm-12 col-xl-6" v-for="(element, index) in cards" :key="index">
        <div class="card">
          <div class="card-header pb-0" v-html="element.title"></div>
          <div class="card-body">
            <p v-text="element.description"></p>
          </div>
        </div>
      </div>
    </VueDraggableNext>
  </ClientOnly>
</template>
<script lang="ts" setup>
import { VueDraggableNext } from 'vue-draggable-next';

import { useCardStore } from '~/store/card';

const store = useCardStore();
const { draggabler } = storeToRefs(store);
const cards = draggabler.value;
</script>
