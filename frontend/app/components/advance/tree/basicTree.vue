<template>
  <div class="col-sm-12 col-xl-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Basic Tree</h5>
      </div>
      <div class="card-body">
        <div id="treeBasic">
          <Tree :nodes="menu" :use-icon="true" />
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { menu } from '~/composables/commen/treeView';
</script>
