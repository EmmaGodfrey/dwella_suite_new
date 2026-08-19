<template>
  <div class="col call-chat-body">
    <div class="card">
      <div class="card-body p-0">
        <div class="row chat-box">
          <div class="col pe-0 chat-right-aside">
            <div class="chat">
              <div class="media chat-header clearfix">
                <img class="rounded-circle" v-if="current.thumb" :src="getImgUrl(current.thumb)" alt="" />
                <div class="media-body">
                  <div class="about">
                    <div class="name">
                      {{ current.name }}
                    </div>
                    <div class="status digits">
                      {{ current.lastSeenDate }}
                    </div>
                  </div>
                </div>
                <ul class="list-inline float-start float-sm-right chat-menu-icons">
                  <li class="list-inline-item">
                    <a href="#"><i class="icon-search"></i></a>
                  </li>
                  <li class="list-inline-item">
                    <a href="#"><i class="icon-clip"></i></a>
                  </li>
                  <li class="list-inline-item">
                    <a href="#"><i class="icon-headphone-alt"></i></a>
                  </li>
                  <li class="list-inline-item">
                    <a href="#"><i class="icon-video-camera"></i></a>
                  </li>
                  <li class="list-inline-item toogle-bar" data-bs-toggle="collapse" data-bs-target="#collapseExample" :class="[isActive ? 'active' : '', 'collapsible']" v-on:click="toggle">
                    <a href="javascript:void(0)"><i class="icon-menu"></i></a>
                  </li>
                </ul>
              </div>
              <div class="chat-history chat-msg-box custom-scrollbar">
                <ul>
                  <li v-for="(chat, index) in current.chat?.messages" :key="index" v-bind:class="{ clearfix: chat.sender == 0 }">
                    <div
                      class="message"
                      v-bind:class="{
                        'other-message pull-right': chat.sender == 0,
                        'my-message': chat.sender != 0,
                      }"
                    >
                      <img class="rounded-circle float-start chat-user-img img-30 text-end" alt="" v-if="current.thumb && chat.sender != 0" v-bind:src="getImgUrl(current.thumb)" />
                      <img class="rounded-circle float-end chat-user-img img-30" alt="" v-if="chat.sender == 0" v-bind:src="getImgUrl('user/1.jpg')" />
                      <div class="message-data text-end" v-bind:class="{ 'text-start': chat.sender == 0 }">
                        <span class="message-data-time">{{ chat.time }}</span>
                      </div>

                      {{ chat.text }}
                    </div>
                  </li>
                </ul>
              </div>
              <ChatChatappAddChat />
            </div>
          </div>
          <div class="col ps-0 chat-menu custom-scrollbar" :class="[isActive ? 'block' : 'none', 'content']" v-show="isActive" id="collapseExample">
            <CommenChatMenu />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { storeToRefs } from 'pinia';

import { useChatStore } from '~/store/chat';

const isActive = ref<boolean>(false);
const store = useChatStore();
const { currentChat: current } = storeToRefs(store);
function getImgUrl(path: string) {
  return '/images/' + path;
}
function toggle() {
  isActive.value = !isActive.value;
}
</script>
