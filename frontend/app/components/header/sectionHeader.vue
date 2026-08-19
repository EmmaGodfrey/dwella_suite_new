<template>
  <div class="main-header-right row m-0">
    <div class="main-header-left">
      <HeaderSidebarView />
    </div>
    <div class="left-menu-header col">
      <ul>
        <li>
          <HeaderSearchBar />
        </li>
      </ul>
    </div>
    <div class="nav-right col pull-right right-menu p-0">
      <ul class="nav-menus" :class="filtered ? 'open' : ''">
        <li>
          <HeaderMaxiMaize />
        </li>
        <li class="language-nav">
          <HeaderLanguageView />
        </li>
        <li class="onhover-dropdown">
          <HeaderBookmarkSearch />
        </li>
        <li class="onhover-dropdown">
          <HeaderNotifiCations />
        </li>
        <li>
          <HeaderModeView />
        </li>
        <li class="onhover-dropdown">
          <HeaderChatView />
        </li>
        <li class="onhover-dropdown p-0">
          <HeaderLogOut />
        </li>
      </ul>
    </div>
    <div class="d-lg-none mobile-toggle pull-right w-auto">
      <Icon name="ion:android-more-horizontal" class="" size="20" @click="collapseFilter()" />
    </div>
  </div>
</template>
<script lang="ts" setup>
defineEmits(['clicked']);
const filtered = ref<boolean>(false);
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
