import { defineStore } from 'pinia';

import model from '~/data/button.json';

interface drop {
  classes: string;
  title: string;
}
interface item {
  classes: string;
}

export const useCommenStore = defineStore('commen', () => {
  const data = ref<drop[]>(model.button);
  const color = ref<drop[]>(model.color);
  const outline = ref<drop[]>(model.outline);
  const gradien = ref<drop[]>(model.gradien);
  const raised = ref<drop[]>(model.raised);
  const color1 = ref<drop[]>(model.color1);
  const outline1 = ref<drop[]>(model.outline1);
  const gradien1 = ref<drop[]>(model.gradien1);
  return {
    data,
    color,
    outline,
    gradien,
    raised,
    color1,
    outline1,
    gradien1,
  };
});
