import { defineStore } from 'pinia';

import table from '~/data/datatable.json';
import datatable from '~/types/datatable';

export const useDatatableStore = defineStore('datatable', () => {
  const data = ref<datatable[]>(table.items);

  return {
    data,
  };
});
