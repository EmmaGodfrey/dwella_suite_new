<template>
  <div class="fade tab-pane" v-bind:class="activeclass === 'pills_shared' ? 'active show' : ''" id="pills-shared" role="tabpanel" aria-labelledby="pills-shared-tab">
    <div class="card mb-0">
      <div class="card-header d-flex">
        <h6 class="mb-0">Shared with me</h6>
        <ul>
          <li>
            <a class="grid-bookmark-view" href="javascript:void(0);">
              <Icon name="akar-icons:grid" class=" " size="20" />
            </a>
          </li>
          <li>
            <a class="list-layout-view" href="javascript:void(0);">
              <Icon name="ic:outline-format-list-bulleted" class=" " size="20" />
            </a>
          </li>
        </ul>
      </div>
      <div class="card-body">
        <div class="details-bookmark text-center"><span>No Bookmarks Found.</span></div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const store = useProjectStore();
const { activeclass } = storeToRefs(store);
</script>
