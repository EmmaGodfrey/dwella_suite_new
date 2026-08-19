<template>
  <div class="col-xl-3 box-col-3 pe-0 xl-30">
    <div class="job-sidebar">
      <a class="btn btn-primary job-toggle" href="javascript:void(0)" @click="collapseFilter()">file filter</a>
      <div class="job-left-aside custom-scrollbar" :class="filtered ? 'open' : ''">
        <div class="file-sidebar">
          <div class="card">
            <div class="card-body">
              <ul>
                <li v-for="(item, index) in data" :key="index">
                  <div class="btn" :class="item.class"><Icon :name="item.icon" class="me-2" size="16" />{{ item.title }}</div>
                </li>
              </ul>
              <hr />
              <ul>
                <li>
                  <div class="btn btn-outline-primary">
                    <Icon name="tabler:database" class="me-2" size="16" />
                    Storage
                  </div>
                  <div class="m-t-15">
                    <div class="progress sm-progress-bar mb-3">
                      <div class="progress-bar bg-primary" role="progressbar" style="width: 25%" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <h6 class="f-w-500">25 GB of 100 GB used</h6>
                  </div>
                </li>
              </ul>
              <hr />
              <ul>
                <li>
                  <div class="btn btn-outline-primary"><Icon name="iconoir:view-grid" class="me-2" size="16" />Pricing plan</div>
                </li>
                <li></li>
                <div class="pricing-plan" v-for="(item, index) in pricing" :key="index">
                  <h6>{{ item.version }}</h6>
                  <h5>{{ item.fre }}</h5>
                  <p>{{ item.space }}</p>
                  <div class="btn btn-outline-primary btn-xs">Selected</div>
                  <img class="bg-img" :src="item.img" alt="" />
                </div>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useFilemanegerStore } from '~/store/filemaneger';

const filtered = ref<boolean>(false);
const store = useFilemanegerStore();
const { sidebar, pricing } = storeToRefs(store);
const data = sidebar.value;

function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
