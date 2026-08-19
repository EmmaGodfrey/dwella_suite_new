<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Directions</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-primary" v-tooltip.top="'Tooltip on top'">Tooltip on top</button>
        <button class="btn btn-primary" v-tooltip.right="'Tooltip on right'">Tooltip on right</button>
        <button class="btn btn-primary" v-tooltip.bottom="'Tooltip on bottom'">Tooltip on bottom</button>
        <button class="btn btn-primary" v-tooltip.left="'Tooltip on left'">Tooltip on left</button>
      </div>
    </div>
  </div>
</template>
