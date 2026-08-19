import { defineStore } from 'pinia';

import orderhistory from '~/data/orderhistory.json';

interface order {
  images: string;
  product1: string;
  product2: string;
  orderStatus: string;
  size: string;
  color: string;
  articlenumber: number;
  units: number;
  price: number;
}

export const useOrderhistoryStore = defineStore('orderhistory', () => {
  const data = ref<order[]>(orderhistory.product);

  return {
    data,
  };
});
