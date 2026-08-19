<template>
  <div class="notification-box">
    <Icon name="ic:sharp-notifications-none" @click="notificationOpen()" size="20" />
    <span class="dot-animated"></span>
  </div>
  <div class="onhover-show-div notification-dropdown" :class="{ active: notification }">
    <ul>
      <li>
        <p class="f-w-700 mb-0">You have 3 Notifications<span class="pull-right badge badge-primary rounded-pill">4</span></p>
      </li>
      <li :class="item.class" v-for="(item, index) in data" :key="index">
        <div class="media">
          <span class="notification-bg" :class="item.span">
            <Icon :name="item.icon" size="20" />
          </span>
          <div class="media-body">
            <p>{{ item.title }}</p>
            <span>{{ item.time }}</span>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>
<script lang="ts" setup>
import { useHeaderStore } from '~/store/header';

const notification = ref<boolean>(false);
const store = useHeaderStore();
const { data } = storeToRefs(store);

function notificationOpen() {
  notification.value = !notification.value;
}
</script>
