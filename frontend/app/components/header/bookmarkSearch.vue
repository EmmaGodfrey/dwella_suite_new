\
<template>
  <div class="bookmark-box">
    <Icon name="ic:baseline-star-border" class="" size="20" />
  </div>
  <div class="onhover-show-div bookmark-flip" :class="bookmarkSearchBox ? 'active' : ''">
    <div class="flip-card">
      <div class="flip-card-inner" :class="bookmarkSearchBox ? 'flipped' : ''">
        <div class="front dropdown-title bookmark-div">
          <h6 class="f-18 mb-0">Bookmark</h6>
          <ul class="bookmark-dropdown pb-0">
            <li class="custom-scrollbar">
              <div class="row">
                <div class="col-4 text-center" v-for="(menuItem, index) in bookmarkItems.slice(0, 8)" :key="index">
                  <div class="bookmark-content">
                    <div class="bookmark-ico">
                      <Icon class="bookmark-icons" size="20" :name="menuItem.icon ?? ''" />
                    </div>
                    <h5 class="mt-2">
                      <router-link :to="{ path: menuItem.path }" class="realname">{{ menuItem.title }}</router-link>
                    </h5>
                  </div>
                </div>
              </div>
            </li>
            <li class="text-center">
              <a class="flip-btn btn btn-primary" id="flip-btn" href="javascript:void(0)" @click="openBookmark"> Add New Bookmark</a>
            </li>
          </ul>
        </div>
        <div class="back dropdown-title bookmark-icon">
          <ul>
            <li>
              <div class="bookmark-dropdown flip-back-content">
                <input type="text" placeholder="search..." @keyup="searchTerms" v-model="terms" />
              </div>
              <div class="bookmark-search custom-scrollbar" :class="!bookmarkSearchResultEmpty ? 'Typeahead-menu is-open' : 'Typeahead-menu'" v-if="searchMenuItems.length">
                <div class="ProfileCard u-cf" v-for="(menuItem, index) in searchMenuItems.slice(0, 8)" :key="index">
                  <div class="ProfileCard-avatar header-search">
                    <Icon :name="menuItem.icon ?? ''" />
                  </div>
                  <div class="ProfileCard-details">
                    <div class="ProfileCard-realName bookmark-realName">
                      <span @click="removeFix()" style="float: left">
                        <router-link :to="{ path: menuItem.path }" class="realname">{{ menuItem.title }}</router-link>
                      </span>
                      <span class="float-right"
                        ><a href="JavaScript:void(0);" @click="addToBookmark(menuItem)"><i class="fa fa-star-o f-18 bookmark-search f-right" :class="menuItem.bookmark ? 'text-warning' : ''"></i></a
                      ></span>
                    </div>
                  </div>
                </div>
              </div>
              <div :class="bookmarkSearchResultEmpty ? 'Typeahead-menu is-open' : 'Typeahead-menu'">
                <div class="tt-dataset tt-dataset-0">
                  <div class="EmptyMessage">Your search turned up 0 results. Opps There are no result found.</div>
                </div>
              </div>
            </li>
            <li>
              <a href="javascript:void(0)" class="d-block flip-back f-w-700" id="flip-back" @click="openBookmark"> Back </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useMenuStore } from '~/store/menu';

import type { menuItems } from '~/types/menu';

const bookmarkSearchBox = ref<boolean>(false);
const bookmarkItems = ref<menuItems[]>([]);
const bookmarkSearchResult = ref<boolean>(false);
const bookmarkSearchResultEmpty = ref<boolean>(false);
const terms = ref<string>('');
const store = useMenuStore();
const { searchTerm } = store;
const { searchData: searchMenuItems, data } = storeToRefs(store);
const menu = data.value;
onMounted(() => {
  menu.filter(items => {
    if (items.bookmark) {
      bookmarkItems.value.push(items);
    }
  });
});
watch(
  () => [searchMenuItems, terms],
  () => {
    terms.value ? addFix() : removeFix();
    if (!searchMenuItems.value.length) bookmarkSearchResultEmpty.value = true;
    else bookmarkSearchResultEmpty.value = false;
  },
  { deep: true },
);
function openBookmark() {
  bookmarkSearchBox.value = !bookmarkSearchBox.value;
  if (!bookmarkSearchBox) removeFix();
}
function removeFix() {
  bookmarkSearchResult.value = false;
  const text = '';
}
function addFix() {
  bookmarkSearchResult.value = true;
}
function searchTerms() {
  searchTerm(terms.value);
}
function addToBookmark(items: menuItems) {
  const index = bookmarkItems.value.indexOf(items);
  if (index === -1 && !items.bookmark) {
    items.bookmark = true;
    bookmarkItems.value.push(items);
    const text = '';
  } else {
    bookmarkItems.value.splice(index, 1);
    items.bookmark = false;
  }
}
</script>
