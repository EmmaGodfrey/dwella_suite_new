import { defineStore } from 'pinia';

import kanban from '~/data/kanban.json';

interface simp {
  title: string;
  list: number;
  place: string;
  image: string;
  priority: string;
  badge: string;
  id: number;
  more: string;
  date: string;
}
interface cust {
  title: string;
  list: number;
  place: string;
  image: string;
  priority: string;
  badge: string;
  id: number;
  date: string;
}

export const useKanbanStore = defineStore('kanban', () => {
  const simple = ref<simp[]>(kanban.simple);
  const custom = ref<cust[]>(kanban.custom);
  const api = ref<simp[]>(kanban.api);

  return {
    simple,
    custom,
    api,
  };
});
