<template>
  <div class="col-sm-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Always Visible Scroll</h5>
      </div>
      <div class="card-body">
        <div class="scroll-bar-wrap">
          <perfect-scrollbar class="visible-scroll always-visible scroll-demo" :settings="settings5">
            <div class="horz-scroll-content">
              <div class="row">
                <div class="col-sm-3" v-for="(item, index) in always" :key="index">
                  <p>{{ item.desc }}</p>
                  <p>{{ item.desc1 }}</p>
                  <p>{{ item.desc2 }}</p>
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
const { always } = storeToRefs(store);
const settings5 = {
  maxScrollbarLength: 60,
  suppressScrollY: true,
  suppressScrollX: true,
};
</script>
