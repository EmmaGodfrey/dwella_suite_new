<template>
  <div class="col-sm-12 col-xl-6 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5>Pie Chart <span class="digits">4</span></h5>
      </div>
      <div class="card-body chart-block overflow-hidden">
        <client-only> <GChart :type="chartType" :data="chartData" :options="chartOptions" :settings="settings" /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
interface Settings {
  packages: string[];
}
const chartType: string = 'WordTree';
const chartData = [
  ['Phrases'],
  ['cats are better than dogs'],
  ['cats eat kibble'],
  ['cats are better than hamsters'],
  ['cats are awesome'],
  ['cats are people too'],
  ['cats eat mice'],
  ['cats meowing'],
  ['cats in the cradle'],
  ['cats eat mice'],
  ['cats in the cradle lyrics'],
  ['cats eat kibble'],
  ['cats for adoption'],
  ['cats are family'],
  ['cats eat mice'],
  ['cats are better than kittens'],
  ['cats are evil'],
  ['cats are weird'],
  ['cats eat mice'],
];
const chartOptions = {
  wordtree: {
    format: 'implicit',
    word: 'cats',
  },

  height: 400,
};
const settings: Settings = {
  packages: ['wordtree'],
};
</script>
