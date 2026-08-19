<template>
  <div class="col call-chat-body">
    <div class="card">
      <div class="card-body p-0">
        <div class="row chat-box">
          <div class="col chat-right-aside">
            <div class="chat">
              <div class="media chat-header clearfix">
                <img class="rounded-circle" v-if="currentChat.thumb" :src="getImgUrl(currentChat.thumb)" alt="" />
                <div class="media-body">
                  <div class="about">
                    <div class="name">
                      {{ currentChat.name }}
                    </div>
                    <div class="status digits">
                      {{ currentChat.lastSeenDate }}
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
              <div class="chat-history">
                <div class="row" v-for="(chat, index) in currentChat.chat?.video" :key="index" v-bind:class="{ clearfix: chat.sender == 0 }">
                  <div class="col text-center pe-0 call-content">
                    <div>
                      <div class="total-time">
                        <h2 class="digits">{{ chat.time }}</h2>
                      </div>
                      <div class="call-icons">
                        <ul class="list-inline">
                          <li class="list-inline-item">
                            <a href="javascript:void(0)"><i class="icon-video-camera"></i></a>
                          </li>
                          <li class="list-inline-item">
                            <a href="javascript:void(0)"><i class="icon-volume"></i></a>
                          </li>
                          <li class="list-inline-item">
                            <a href="javascript:void(0)"><i class="icon-user"></i></a>
                          </li>
                        </ul>
                      </div>
                      <button class="btn btn-danger btn-block btn-lg">END CALL</button>
                      <div class="receiver-img"><img src="/images/other-images/receiver-img.jpg" alt="" /></div>
                    </div>
                  </div>
                  <div class="col-sm-6 caller-img-sec">
                    <div class="caller-img"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col pl-0 chat-menu custom-scrollbar" :class="[isActive ? 'block' : 'none', 'content']" v-show="isActive" id="collapseExample">
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
const { currentChat } = storeToRefs(useChatStore());

function getImgUrl(path: string) {
  return '/images/' + path;
}
function toggle() {
  isActive.value = !isActive.value;
}
</script>
