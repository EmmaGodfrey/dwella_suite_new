import { defineStore } from 'pinia';

import owlcarousel from '~/data/owlcarousel.json';

interface image {
  img: string;
}

export const useOwlcarouselStore = defineStore('owlcarousel', () => {
  const items = ref<image[]>(owlcarousel.items);
  const item = ref<image[]>(owlcarousel.item);

  return {
    item,
    items,
  };
});
