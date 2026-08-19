import { defineStore } from 'pinia';

import chat from '~/data/chat.json';
import chatapp from '~/types/chat';

interface chat {
  id: number;
  users: number[];
  lastMessageTime: string;
  messages: msg[];
  video: video[];
}
interface msg {
  sender?: number;
  time: string;
  text?: string;
}
interface video {
  sender: number;
  time: string;
  thumb: string;
}
interface addchat {
  addchat: object;
}
export const useChatStore = defineStore('chat', () => {
  const users = ref<chatapp[]>(chat.data);
  const serchUser = ref(chat.data);
  const all = ref<chatapp[]>(chat.data);
  const chats = ref<chat[]>(chat.chat);
  const activeuser = ref<chatapp>(chat.data[1]!);

  function setSerchUsers(item: string) {
    serchUser.value = all.value.filter(search => {
      if (search.name.toLowerCase().search(item.toLowerCase()) !== -1 && search.id !== 0) return search;
    });
  }

  function setActiveuser(user: chatapp) {
    activeuser.value = user;
  }

  const currentChat = computed(() => {
    const chat = chats.value.find(chat => {
      if (chat.id === activeuser.value.id) return chat;
    });
    const user = users.value.find(user => {
      if (user.id === activeuser.value.id) return user;
    });
    return { ...user, chat: chat };
  });

  function addChat(user: string) {
    const today = new Date().toLocaleString('en-US', { hour: 'numeric', minute: 'numeric', hour12: true });
    const id = activeuser.value;
    const addchat: chat | undefined = chats.value.find(chat => chat.id === activeuser.value.id);
    if (!addchat) return;
    addchat.messages.push({ sender: 0, time: today.toLowerCase(), text: user });
    setTimeout(function () {
      addchat.messages.push({ sender: activeuser.value.id, time: today.toLowerCase(), text: '... I will text you later.' });
    }, 1000);
  }
  return {
    serchUser,
    activeuser,
    all,
    users,
    chats,
    setSerchUsers,
    currentChat,
    setActiveuser,
    addChat,
  };
});
