import { defineStore } from 'pinia';

import pagination from '~/data/pagination.json';

interface pagenation {
  class?: string;
  color?: string;
  size?: string;
}

export const usePaginationStore = defineStore('pagination', () => {
  const alignment = ref<pagenation[]>(pagination.alignment);
  const color = ref<pagenation[]>(pagination.color);
  const size = ref<pagenation[]>(pagination.size);

  return {
    alignment,
    color,
    size,
  };
});
