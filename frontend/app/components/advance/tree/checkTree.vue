<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Checkbox Tree</h5>
      </div>
      <div class="card-body">
        <div id="treecheckbox">
          <Tree :nodes="tree" :use-icon="false" :use-checkbox="true" />
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { tree } from '~/composables/commen/treeView';
</script>
