import { defineStore } from 'pinia';

import model from '~/data/uikit.json';

interface desc {
  desc: string;
}
interface spinn {
  title: string;
  class: string;
}
interface items {
  classes: string;
}
interface drop {
  classes: string;
  title: string;
}

export const useUikitStore = defineStore('social', () => {
  const data = ref<desc[]>(model.data);
  const spinner = ref<spinn[]>(model.spinner);
  const dropdown = ref<items[]>(model.dropdown);
  const dropdown1 = ref<drop[]>(model.dropdown1);
  return {
    data,
    spinner,
    dropdown,
    dropdown1,
  };
});
