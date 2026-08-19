import { defineStore } from 'pinia';

import email from '~/data/email.json';
import emailinbox from '~/types/emailinbox';

export const useEmaillStore = defineStore('emaill', () => {
  const data = ref<emailinbox[]>(email.data);

  return {
    data,
  };
});
