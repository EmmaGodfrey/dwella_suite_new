import { defineStore } from 'pinia';

import support from '~/data/support.json';
import supportDetails from '~/types/supportDetails';
import supportticket from '~/types/supportticket';

export const useSupportStore = defineStore('support', () => {
  const item = ref<supportDetails[]>(support.items);
  const ticket = ref<supportticket[]>(support.ticket);

  return {
    item,
    ticket,
  };
});
