import { defineStore } from 'pinia';

import dashboard from '~/data/dashboard.json';

interface item {
  img: string;
  title: string;
  date: string;
  quantity: string;
  value: string;
  rate: string;
}
interface items {
  id: string;
  name: string;
  src1: string;
  name1: string;
}
interface active {
  date: string;
  title: string;
  desc: string;
  pill?: string;
  pin?: boolean;
  img?: sub[];
}
interface sub {
  img?: string;
}
export const useDashboardStore = defineStore('dashboard', () => {
  const data = ref<item[]>(dashboard.order);
  const cards = ref<items[]>(dashboard.cards);
  const card = ref<items[]>(dashboard.cards1);
  const activity = ref<active[]>(dashboard.activity);
  return {
    data,
    card,
    cards,
    activity,
  };
});
