import { defineStore } from 'pinia';

import header from '~/data/header.json';

interface item {
  title: string;
  time: string;
  icon: string;
  class: string;
  span: string;
}
interface items {
  img: string;
  name: string;
  about: string;
  time: string;
}
interface bre {
  icon: string;
  path: string;
  tooltip: string;
}
export const useHeaderStore = defineStore('header', () => {
  const data = ref<item[]>(header.notification);
  const chat = ref<items[]>(header.chat);
  const bread = ref<bre[]>(header.bread);
  return {
    data,
    chat,
    bread,
  };
});
