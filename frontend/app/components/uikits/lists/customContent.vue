<template>
  <div class="col-sm-12 col-xl-12">
    <div class="card custom-content">
      <div class="card-header pb-0">
        <h5>Custom content</h5>
      </div>
      <div class="card-body">
        <div class="list-group">
          <a class="list-group-item list-group-item-action flex-column align-items-start active" href="javascript:void(0)">
            <div class="d-flex w-100 justify-content-between">
              <h5 class="mb-1">{{ title }}</h5>
              <small>{{ day }}</small>
            </div>
            <p class="mb-1">{{ desc }}</p>
            <small>{{ desc1 }}</small> </a
          ><a class="list-group-item list-group-item-action flex-column align-items-start" href="javascript:void(0)">
            <div class="d-flex w-100 justify-content-between">
              <h5 class="mb-1">{{ title }}</h5>
              <small class="text-muted">{{ day }}</small>
            </div>
            <p class="mb-1">{{ desc }}</p>
            <small class="text-muted">{{ desc1 }}</small> </a
          ><a class="list-group-item list-group-item-action flex-column align-items-start" href="javascript:void(0)">
            <div class="d-flex w-100 justify-content-between">
              <h5 class="mb-1">{{ title }}</h5>
              <small class="text-muted">{{ day }}</small>
            </div>
            <p class="mb-1">{{ desc }}</p>
            <small class="text-muted">{{ desc1 }}</small>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const title = ref<string>('List group item heading');
const day = ref<string>('3 days ago');
const desc = ref<string>('Donec id elit non mi porta gravida at eget metus. Maecenas sed diam eget risus varius blandit.');
const desc1 = ref<string>('Donec id elit non mi porta.');
</script>
