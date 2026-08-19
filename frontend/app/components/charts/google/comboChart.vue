<template>
  <div class="col-sm-12 box-col-12">
    <div class="card">
      <div class="card-header">
        <h5>Combo Chart</h5>
      </div>
      <div class="card-body chart-block">
        <client-only> <GChart class="chart-overflow" id="combo-chart" type="ComboChart" :data="comboChart.chartData_1" :options="comboChart.options_1" /></client-only>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const primary = ref<string>(useCookie('primary_color').value || '#24695c');
const secondary = ref<string>(useCookie('secondary_color').value || '#ba895d');
const comboChart = {
  chartData_1: [
    ['Month', 'Bolivia', 'Ecuador', 'Madagascar', 'Papua New Guinea', 'Rwanda', 'Average'],
    ['2004/05', 165, 938, 522, 998, 450, 614.6],
    ['2005/06', 135, 1120, 599, 1268, 288, 682],
    ['2006/07', 157, 1167, 587, 807, 397, 623],
    ['2007/08', 139, 1110, 615, 968, 215, 609.4],
    ['2008/09', 136, 691, 629, 1026, 366, 569.6],
  ],
  options_1: {
    title: 'Monthly Coffee Production by Country',
    vAxis: { title: 'Cups' },
    hAxis: { title: 'Month' },
    seriesType: 'bars',
    series: { 5: { type: 'line' } },
    height: 500,
    fullWidth: true,
    colors: [primary.value, secondary.value, '#222222', '#717171', '#e2c636'],
  },
};
</script>
