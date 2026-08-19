import { defineStore } from 'pinia';

import task from '~/data/task.json';

interface data {
  title: string;
  desc: string;
}

export const useTaskStore = defineStore('task', () => {
  const items = ref<data[]>(task.data);

  return {
    items,
  };
});
