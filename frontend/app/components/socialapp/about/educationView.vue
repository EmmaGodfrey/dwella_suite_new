<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header social-header">
        <h5>
          <span class="f-w-600">Education and Employement</span><span class="pull-right"><Icon name="lucide:ellipsis-vertical"></Icon></span>
        </h5>
      </div>
      <div class="card-body pt-0">
        <div class="row details-about" v-for="(item, index) in data" :key="index">
          <div class="col-sm-6">
            <div class="your-details">
              <h6 class="f-w-600">{{ item.title }}</h6>
              <p>{{ item.year }}</p>
              <p>{{ item.desc }}</p>
            </div>
          </div>
          <div class="col-sm-6">
            <div class="your-details your-details-xs">
              <h6 class="f-w-600">{{ item.title1 }}</h6>
              <p>{{ item.year1 }}</p>
              <p>{{ item.desc1 }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useSocialStore } from '~/store/social';

const store = useSocialStore();
const { education } = storeToRefs(store);
const data = education.value;
</script>
