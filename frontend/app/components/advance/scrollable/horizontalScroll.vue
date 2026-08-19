<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Horizontal Scroll</h5>
      </div>
      <div class="card-body">
        <div class="scroll-bar-wrap">
          <perfect-scrollbar class="horizontal-scroll scroll-demo" v-once :settings="settings4">
            <div class="horz-scroll-content">
              <div class="row">
                <div class="col-sm-3" v-for="(item, index) in horizontal" :key="index">
                  <p>{{ item.desc }}</p>
                </div>
              </div>
            </div>
          </perfect-scrollbar>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useScrollableStore } from '~/store/scrollable';

const store = useScrollableStore();
const { data } = storeToRefs(store);
const horizontal = data.value;

const settings4 = {
  maxScrollbarLength: 60,
  suppressScrollY: true,
  suppressScrollX: false,
};
</script>
