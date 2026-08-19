import { defineStore } from 'pinia';

import invoice from '~/data/invoice.json';
import Invoice from '~/types/invoice';
import pricing from '~/types/pricing';
import wishlist from '~/types/wishlist';

export const useInvoiceStore = defineStore('invoice', () => {
  const data = ref<Invoice[]>(invoice?.invoice);
  const simplePricing = ref<pricing[]>(invoice?.simplePricing);
  const pricing = ref<pricing[]>(invoice?.pricing);
  const wishlist = ref<wishlist[]>(invoice?.whislist);

  return {
    data,
    simplePricing,
    pricing,
    wishlist,
  };
});
