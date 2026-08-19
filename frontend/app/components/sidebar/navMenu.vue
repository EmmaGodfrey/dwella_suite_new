<template>
  <li class="back-btn">
    <div class="mobile-back text-end"><span>Back</span> <i class="fa fa-angle-right ps-2" aria-hidden="true"></i></div>
  </li>
  <li
    v-for="(menu, index) in menuItem"
    :key="index"
    :class="{
      'sidebar-main-title': menu.type == 'headtitle',
    }"
    class="dropdown d-block"
  >
    <div v-if="menu.type == 'headtitle'">
      <h6 class="lan-1">{{ menu.headTitle1 }}</h6>
    </div>
    <a href="javascript:void(0)" :class="{ active: menu.active }" class="nav-link menu-title" v-if="menu.type == 'sub'" @click="setNavActive(menu)">
      <Icon :name="menu.icon ?? ''" class="sidebar-icons" size="20" />
      <span>
        {{ $t(menu.title ?? '') }}
      </span>
      <div class="according-menu" v-if="menu.children">
        <i class="pull-right" :class="[menu.active ? 'fa fa-angle-down' : 'fa fa-angle-right']"></i>
      </div>
    </a>
    <nuxt-link :to="menu.path" class="nav-link menu-title" :class="{ active: menu.active }" v-if="menu.type == 'link'" @click="setNavActive(menu)">
      <Icon :name="menu.icon ?? ''" class="sidebar-icons" size="20" />
      <span class="menu1">
        {{ $t(menu.title ?? '') }}
      </span>
      <Icon name="tabler:chevron-right" v-if="menu.children" class="" size="20" />
    </nuxt-link>
    <a :href="menu.path" class="sidebar-link sidebar-title" v-if="menu.type == 'extLink'" @click="setNavActive(menu)">
      <Icon :name="menu.icon ?? ''" class="top sidebar-icons"></Icon>
      <span>
        {{ $t(menu.title ?? '') }}
      </span>
      <i class="fa fa-angle-right pull-right" v-if="menu.children"></i>
    </a>
    <a :href="menu.path" target="_blank" class="sidebar-link sidebar-title" v-if="menu.type == 'extTabLink'" @click="setNavActive(menu)">
      <Icon :name="menu.icon ?? ''" class="top sidebar-icons"></Icon>
      <span>
        {{ $t(menu.title!) }}
      </span>
      <i class="fa fa-angle-right pull-right" v-if="menu.children"></i>
    </a>
    <ul class="nav-submenu menu-content" v-if="menu.children" :class="{ 'menu-open d-block': menu.active }">
      <li v-for="(childrenItem, index) in menu.children" :key="index">
        <a class="submenu-title" href="javascript:void(0)" v-if="childrenItem.type == 'sub'" :class="{ active: childrenItem.active }" @click="setNavActive(childrenItem)">
          {{ $t(childrenItem.title ?? '') }}
          <label :class="'badge badge-' + childrenItem.badgeType + ' pull-right'" v-if="childrenItem.badgeType">{{ childrenItem.badgeValue }}</label>

          <i class="pull-right" :class="[childrenItem.active ? 'fa fa-angle-down' : 'fa fa-angle-right']" v-if="childrenItem.children"></i>
        </a>
        <nuxt-link class="submenu-title" :to="childrenItem.path" :class="{ active: childrenItem.active }" v-if="childrenItem.type == 'link'" @click="setNavActive(childrenItem)">
          {{ $t(childrenItem.title ?? '') }}
          <label :class="'badge badge-' + childrenItem.badgeType + ' pull-right'" v-if="childrenItem.badgeType">{{ childrenItem.badgeValue }}</label>
          <i class="fa fa-angle-right pull-right mt-1" v-if="childrenItem.children"></i>
        </nuxt-link>
        <a :href="childrenItem.path" v-if="childrenItem.type == 'extLink'" class="submenu-title">
          {{ $t(childrenItem.title ?? '') }}
          <label :class="'badge badge-' + childrenItem.badgeType + ' pull-right'" v-if="childrenItem.badgeType">{{ childrenItem.badgeValue }}</label>
          <i class="fa fa-angle-right pull-right mt-1" v-if="childrenItem.children"></i>
        </a>
        <a class="submenu-title" :href="childrenItem.path" target="_blank" v-if="childrenItem.type == 'extTabLink'">
          {{ $t(childrenItem.title ?? '') }}
          <label :class="'badge badge-' + childrenItem.badgeType + ' pull-right'" v-if="childrenItem.badgeType">{{ childrenItem.badgeValue }}</label>
          <i class="fa fa-angle-right pull-right mt-1" v-if="childrenItem.children"></i>
        </a>
        <ul class="nav-sub-childmenu submenu-content" v-if="childrenItem.children" :class="{ opensubchild: childrenItem.active }">
          <li v-for="(childrenSubItem, index) in childrenItem.children" :key="index">
            <nuxt-link :to="childrenSubItem.path" v-if="childrenSubItem.type == 'link'" exact>
              {{ $t(childrenSubItem.title ?? '') }}
              <label :class="'badge badge-' + childrenSubItem.badgeType + ' pull-right'" v-if="childrenSubItem.badgeType">{{ childrenSubItem.badgeValue }}</label>
              <i class="fa fa-angle-right pull-right" v-if="childrenSubItem.children"></i>
            </nuxt-link>
            <nuxt-link :to="childrenSubItem.path" v-if="childrenSubItem.type == 'extLink'">
              {{ $t(childrenSubItem.title ?? '') }}
              <label :class="'badge badge-' + childrenSubItem.badgeType + ' pull-right'" v-if="childrenSubItem.badgeType">{{ childrenSubItem.badgeValue }}</label>
              <i class="fa fa-angle-right pull-right" v-if="childrenSubItem.children"></i>
            </nuxt-link>
            <nuxt-link :to="childrenSubItem.path" v-if="childrenSubItem.type == 'extLink'">
              {{ $t(childrenSubItem.title ?? '') }}
              <label :class="'badge badge-' + childrenSubItem.badgeType + ' pull-right'" v-if="childrenSubItem.badgeType">{{ childrenSubItem.badgeValue }}</label>
              <i class="fa fa-angle-right pull-right" v-if="childrenSubItem.children"></i>
            </nuxt-link>
          </li>
        </ul>
      </li>
    </ul>
  </li>
</template>
<script lang="ts" setup>
import { useMenuStore } from '~/store/menu';

let store = useMenuStore();
let { data } = storeToRefs(store);
let menuItem = data.value;
let { setNavActive } = store;
</script>
