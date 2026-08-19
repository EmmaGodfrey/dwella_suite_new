<template>
  <input class="text" placeholder="Search here....." :class="filtered ? 'open' : ''" @keyup="searchTerm" v-model="termss" title="" autofocus />

  <div :class="searchResult ? 'Typeahead-menu is-open ' : 'Typeahead-menu '" v-if="menuItems.length">
    <div class="ProfileCard u-cf" v-for="(menuItem, index) in menuItems.slice(0, 8)" :key="index">
      <div class="ProfileCard-avatar header-search">
        <Icon :name="menuItem.icon ?? ''" class="" size="20" />
      </div>
      <div class="ProfileCard-details">
        <div class="ProfileCard-realName">
          <span @click="removeFix()"
            ><router-link :to="{ path: menuItem.path }" class="realname">{{ menuItem.title }}</router-link></span
          >
        </div>
      </div>
    </div>
  </div>
  <div :class="searchResultEmpty ? 'Typeahead-menu is-open' : 'Typeahead-menu'">
    <div class="tt-dataset tt-dataset-0">
      <div class="EmptyMessage">Your search turned up 0 results. Opps There are no result found.</div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { storeToRefs } from 'pinia';

import { useMenuStore } from '~/store/menu';

const filtered = ref<boolean>(false);

const termss = ref<string>('');
const store = useMenuStore();
const { searchDatas: menuItems } = storeToRefs(store);
const { searchTerms } = store;
const searchResult = ref<boolean>(false);
const searchResultEmpty = ref<boolean>(false);

watch(
  () => [menuItems, termss],
  () => {
    termss.value ? addFix() : removeFix();
    if (!menuItems.value.length) searchResultEmpty.value = true;
    else searchResultEmpty.value = false;
  },
  { deep: true },
);

function searchTerm() {
  searchTerms(termss.value);
}
function addFix() {
  searchResult.value = true;
}
function removeFix() {
  searchResult.value = false;
  termss.value = '';
}
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
