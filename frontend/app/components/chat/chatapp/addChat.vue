<template>
  <div class="chat-message clearfix">
    <div class="row">
      <div class="col-xl-12 d-flex">
        <div class="smiley-box bg-primary">
          <div class="picker">
            <img src="/images/smiley.png" alt="" />
          </div>
        </div>
        <div class="input-group text-box">
          <input class="form-control input-txt-bx" id="message-to-send" v-model="text" v-on:keyup.enter="addChats()" type="text" name="message-to-send" placeholder="Type a message......" />
          <button @click="addChats()" class="btn btn-primary input-group-text" type="button">SEND</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useChatStore } from '~/store/chat';

const text = ref<string>('');
const store = useChatStore();
const { addChat } = store;
function addChats() {
  var container = document.querySelector('.chat-history') as HTMLInputElement;
  setTimeout(function () {
    container.scrollBy({ top: 200, behavior: 'smooth' });
  }, 310);
  setTimeout(function () {
    container.scrollBy({ top: 200, behavior: 'smooth' });
  }, 1100);
  if (text.value !== '') {
    addChat(text.value);
    text.value = '';
  }
}
</script>
