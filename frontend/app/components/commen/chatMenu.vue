<template>
  <ul class="nav nav-tabs border-tab nav-primary" id="info-tab" role="tablist">
    <li class="nav-item">
      <a class="nav-link active" id="info-home-tab" data-bs-toggle="tab" href="#info-home" role="tab" aria-selected="true">CALL</a>
      <div class="material-border"></div>
    </li>
    <li class="nav-item">
      <a class="nav-link" id="profile-info-tab" data-bs-toggle="tab" href="#info-profile" role="tab" aria-selected="false">STATUS</a>
      <div class="material-border"></div>
    </li>
    <li class="nav-item">
      <a class="nav-link" id="contact-info-tab" data-bs-toggle="tab" href="#info-contact" role="tab" aria-selected="false">PROFILE</a>
      <div class="material-border"></div>
    </li>
  </ul>
  <div class="tab-content" id="info-tabContent">
    <div class="tab-pane fade show active" id="info-home" role="tabpanel" aria-labelledby="info-home-tab">
      <div class="people-list">
        <ul class="list digits custom-scrollbar">
          <li class="clearfix" v-for="(user, index) in user" :key="index" @click="setActiveUser(user)">
            <div class="d-flex align-items-center">
              <img class="rounded-circle user-image" :src="getImgUrl(user.thumb)" alt="" />
              <div class="flex-grow-1">
                <div class="about">
                  <div class="name">{{ user.name }}</div>
                  <div class="status"><i class="fa" :class="user.icon"></i> {{ user.lastSeenDate }}</div>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
    <div class="tab-pane fade" id="info-profile" role="tabpanel" aria-labelledby="profile-info-tab">
      <CommenStatusView />
    </div>
    <div class="tab-pane fade" id="info-contact" role="tabpanel" aria-labelledby="contact-info-tab">
      <CommenProfileView />
    </div>
  </div>
</template>
<script lang="ts" setup>
import { computed } from 'vue';

import { useChatStore } from '~/store/chat';
import chatapp from '~/types/chat';

const store = useChatStore();
const { users } = storeToRefs(store);
const { setActiveuser } = store;

const user = computed(() =>
  users.value.filter(function (user) {
    if (user.id !== 0) return user;
  }),
);
function getImgUrl(path: string) {
  return '/images/' + path;
}
function setActiveUser(user: chatapp) {
  setActiveuser(user);
}
</script>
