import { defineStore } from 'pinia';

import scrollable from '~/data/scrollable.json';
import horizontalscroll from '~/types/horizontalscroll';

interface always {
  id: number;
  desc: string;
  desc1: string;
  desc2: string;
}
interface vertical {
  id: number;
  desc: string;
}

export const useScrollableStore = defineStore('scrollable', () => {
  const data = ref<horizontalscroll[]>(scrollable.horizontalscroll);
  const always = ref<always[]>(scrollable.alwaysVisible);
  const vertical = ref<vertical[]>(scrollable.verticalscroll);
  return {
    data,
    always,
    vertical,
  };
});
