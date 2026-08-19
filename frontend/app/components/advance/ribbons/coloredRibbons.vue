<template>
  <div class="row">
    <div class="col-sm-12 col-xl-12">
      <div class="card">
        <div class="card-header pb-0">
          <h5>Colored breadcrumb</h5>
          <span>use class <code>.breadcrumb-colored .bg-primary</code></span>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in ribbon" :key="index">
              <div class="card ribbon-wrapper">
                <div class="card-body">
                  <div class="ribbon ribbon-primary ribbon-space-bottom">Ribbon</div>
                  <p>{{ item.lorn }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="col-sm-12 col-md-6 col-lg-4" v-for="(item, index) in ribbobItem" :key="index">
      <div class="ribbon-wrapper card">
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
const { data, left } = storeToRefs(store);
const ribbon = data.value;
const ribbobItem = left.value;
</script>
