<template>
  <div class="container-fluid">
    <div class="page-header">
      <div class="row">
        <div class="col-sm-6">
          <h3 class="bread">{{ title }}</h3>
          <ol class="breadcrumb">
            <li class="breadcrumb-item">
              <nuxt-link :to="{ path: '/' }">Home</nuxt-link>
            </li>
            <li class="breadcrumb-item" v-if="sub">{{ sub }}</li>
            <li class="breadcrumb-item" v-if="main">{{ main }}</li>
            <li class="breadcrumb-item active" v-if="title">{{ title }}</li>
          </ol>
        </div>
        <div class="col-sm-6">
          <div class="bookmark">
            <ul>
              <li v-for="(item, index) in data" :key="index">
                <nuxt-link :to="item.path" data-container="body" data-bs-placement="top" title="Bookmark">
                  <Icon :name="item.icon" class="" size="20" />
                </nuxt-link>
              </li>
              <li>
                <a href="javascript:void(0)">
                  <Icon name="ic:baseline-star-border" @click="collapseFilter()" class="" size="20" />
                </a>
                <form class="form-inline search-form">
                  <div class="form-group form-control-search" :class="filtered ? 'open' : ''">
                    <HeaderBreadcrubsSearch />
                  </div>
                </form>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useHeaderStore } from '~/store/header';
import type { BreadcrumbsProps } from '~/types/common';

const props = defineProps<BreadcrumbsProps>();
const filtered = ref<boolean>(false);
const store = useHeaderStore();
const { bread } = storeToRefs(store);
const data = bread.value;
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
