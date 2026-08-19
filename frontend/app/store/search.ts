import { defineStore } from 'pinia';

import search from '~/data/search.json';

interface data {
  id: number;
  title: string;
  desc: string;
  link: string;
}
interface data1 {
  id: number;
  title: string;
  desc: string;
  rating: string;
  rating1: string;
  link: string;
}

export const useSearchStore = defineStore('search', () => {
  const data = ref<data[]>(search.data);
  const data1 = ref<data1[]>(search.data1);

  return {
    data,
    data1,
  };
});
