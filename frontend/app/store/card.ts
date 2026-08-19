import { defineStore } from 'pinia';

import card from '~/data/card.json';

interface creative {
  id?: number;
  title?: string;
  desc?: string;
  header?: string;
  card?: string;
  class?: string;
}
interface basic {
  title: string | number;
  description: string;
}
interface card {
  title?: string;
  color?: string;
  body?: string;
  class?: string;
  footer?: string;
  description: string;
}

export const useCardStore = defineStore('card', () => {
  const creative = ref<creative[]>(card?.creative);
  const draggabler = ref<basic[]>(card.draggable);
  const basic = ref<basic[]>(card.basic);
  const footer = ref<card[]>(card.footer);
  const cardbody = ref<card[]>(card.cardbody);

  return {
    creative,
    draggabler,
    basic,
    footer,
    cardbody,
  };
});
