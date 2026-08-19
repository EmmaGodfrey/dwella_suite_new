import { defineStore } from 'pinia';

import widgets from '~/data/widgets.json';
import employe from '~/types/employe';
import productcart from '~/types/productcart';

interface item {
  day: string;
  icon: string;
  num: string;
  total: string;
}
interface items {
  class: string;
  alfabet: string;
  title: string;
  date: string;
  time: string;
}
interface socials {
  icon: string;
  title: string;
  post: string;
  like: string;
}
interface sub {
  img: string;
  daily: string;
  month: string;
  week: string;
}
export const useWidgetsStore = defineStore('widgets', () => {
  const data = ref<item[]>(widgets.data);

  const data1 = ref<item[]>(widgets.pending);
  const recent = ref<items[]>(widgets.recent);
  const social = ref<socials[]>(widgets.social);
  const brow = ref<sub[]>(widgets.browser);
  const product = ref<productcart[]>(widgets.product);
  const employe = ref<employe[]>(widgets.employe);

  return {
    data,
    data1,
    recent,
    social,
    brow,
    product,
    employe,
  };
});
