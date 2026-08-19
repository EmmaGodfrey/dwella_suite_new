import { defineStore } from 'pinia';

import ribbon from '~/data/ribbon.json';
import ribbonview from '~/types/ribbonview';

export const useRibbonStore = defineStore('ribbon', () => {
  const data = ref<ribbonview[]>(ribbon.colored);
  const left = ref<ribbonview[]>(ribbon.left);
  const right = ref<ribbonview[]>(ribbon.right);
  const verticalLeft = ref<ribbonview[]>(ribbon.verticalleft);
  const bookmark = ref<ribbonview[]>(ribbon.bookmark);
  const verticalRight = ref<ribbonview[]>(ribbon.verticalright);
  const clip = ref<ribbonview[]>(ribbon.clip);
  const item = ref<ribbonview[]>(ribbon.ribbon);
  return {
    data,
    left,
    right,
    verticalLeft,
    bookmark,
    verticalRight,
    clip,
    item,
  };
});
