<template>
  <div class="col-xl-6 xl-50 box-col-12">
    <div class="widget-joins card widget-arrow">
      <div class="row">
        <div class="col-sm-6 pe-0" v-for="(item, index) in data" :key="index">
          <div class="media border-after-xs">
            <div class="align-self-center me-3">
              <span class="widget-t mb-1">Sale</span>
              <h5 class="mb-0">{{ item.day }}</h5>
            </div>
            <div class="media-body align-self-center">
              <Icon :name="item.icon" class="font-primary" size="20" />
            </div>
            <div class="media-body counter1">
              <h5 class="mb-0">
                $<span class="counter">
                  <CommenNumberAnimations :data="item.num" />
                </span>
              </h5>
              <span class="mb-1">{{ item.total }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-xl-6 xl-50 box-col-12">
    <div class="widget-joins card">
      <div class="row">
        <div class="col-sm-6 pe-0" v-for="(item, index) in data1" :key="index">
          <div class="media border-after-xs">
            <div class="align-self-center me-3">{{ item.total }}<i class="fa fa-angle-up ms-2"> </i></div>
            <div class="media-body details ps-3">
              <span class="mb-1">{{ item.day }}</span>
              <h5 class="mb-0 counter">
                <CommenNumberAnimations :data="item.num" />
              </h5>
            </div>
            <div class="media-body align-self-center">
              <Icon :name="item.icon" class="font-primary float-end ms-2" size="20" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useWidgetsStore } from '~/store/widgets';

const store = useWidgetsStore();
const { data, data1 } = storeToRefs(store);
</script>
