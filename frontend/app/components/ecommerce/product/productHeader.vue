<template>
  <div :class="filtered ? 'container-fluid product-wrapper sidebaron' : 'container-fluid product-wrapper'">
    <div class="product-grid">
      <div class="feature-products">
        <div class="row m-b-10">
          <div class="col-md-3 col-sm-2 products-total">
            <div class="square-product-setting d-inline-block">
              <a class="icon-grid grid-layout-view" @click="gridView()">
                <Icon name="iconoir:view-grid" class="" size="20" />
              </a>
            </div>
            <div class="square-product-setting d-inline-block">
              <a class="icon-grid m-0 list-layout-view" @click="listView()">
                <Icon name="ic:baseline-format-list-bulleted" class="" size="20" />
              </a>
            </div>
            <div class="grid-options d-inline-block">
              <ul>
                <li @click="grid2(true)">
                  <a class="product-2-layout-view" data-original-title="" title=""><span class="line-grid line-grid-1 bg-primary"></span><span class="line-grid line-grid-2 bg-primary"></span></a>
                </li>
                <li @click="grid3()">
                  <a class="product-3-layout-view" data-original-title="" title=""
                    ><span class="line-grid line-grid-3 bg-primary"></span><span class="line-grid line-grid-4 bg-primary"></span><span class="line-grid line-grid-5 bg-primary"></span
                  ></a>
                </li>
                <li @click="grid4()">
                  <a class="product-4-layout-view" data-original-title="" title=""
                    ><span class="line-grid line-grid-6 bg-primary"></span><span class="line-grid line-grid-7 bg-primary"></span><span class="line-grid line-grid-8 bg-primary"></span
                    ><span class="line-grid line-grid-9 bg-primary"></span
                  ></a>
                </li>
                <li @click="grid6()">
                  <a class="product-6-layout-view" data-original-title="" title=""
                    ><span class="line-grid line-grid-10 bg-primary"></span><span class="line-grid line-grid-11 bg-primary"></span><span class="line-grid line-grid-12 bg-primary"></span
                    ><span class="line-grid line-grid-13 bg-primary"></span><span class="line-grid line-grid-14 bg-primary"></span><span class="line-grid line-grid-15 bg-primary"></span
                  ></a>
                </li>
              </ul>
            </div>
            <span class="d-none-productlist filter-toggle" @click="collapseFilter()">
              <h6>
                Filters<span class="ms-2">
                  <Icon name="octicon:chevron-down-12" class="middle" size="20" />
                </span>
              </h6>
            </span>
          </div>
          <EcommerceProductLength />
        </div>
        <div class="row">
          <div class="col-md-12">
            <div class="pro-filter-sec">
              <div class="product-sidebar" :class="filtered ? 'open' : ''">
                <div class="filter-section">
                  <div class="card">
                    <div class="card-header">
                      <h6 class="mb-0 f-w-600">
                        Filters
                        <span class="pull-right" @click="collapseFilter()">
                          <i class="fa fa-chevron-down toggle-data"></i>
                        </span>
                      </h6>
                    </div>
                    <EcommerceProductFilterBar @allFilters="allFilter" />
                  </div>
                </div>
              </div>
              <div class="product-search">
                <form>
                  <div class="form-group m-0">
                    <input class="form-control" type="text" placeholder="Search.." />
                    <i class="fa fa-search"></i>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
      <EcommerceProductProdectDetail />
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProductsStore } from '~/store/products';

import type { product } from '~/types/products';

const filtered = ref<boolean>(false);
const allFilters = ref<object[]>([]);
const store = useProductsStore();
const { grid2, grid3, grid4, grid6, listView, setTags } = store;
function collapseFilter() {
  filtered.value = !filtered.value;
}
function gridView() {
  grid4();
}
function allFilter(selectedVal: product[]) {
  allFilters.value = selectedVal;
  setTags(selectedVal.map(product => String(product)));
}
</script>
