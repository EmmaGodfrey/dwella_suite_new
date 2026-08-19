<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Currency Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(cur, index) in currencyIcons" :key="index" v-on:click="iconBar(cur.name)"><i :class="'fa fa-' + cur.name"></i>{{ cur.name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const currencyIcons = ref([
  { name: 'bitcoin' },
  { name: 'btc' },
  { name: 'cny' },
  { name: 'dollar' },
  { name: 'eur' },
  { name: 'euro' },
  { name: 'gbp' },
  { name: 'inr' },
  { name: 'jpy' },
  { name: 'krw' },
  { name: 'money' },
  { name: 'rmb' },
  { name: 'rouble' },
  { name: 'rub' },
  { name: 'ruble' },
  { name: 'rupee' },
  { name: 'try' },
  { name: 'turkish-lira' },
  { name: 'usd' },
  { name: 'won' },
  { name: 'yen' },
]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>
