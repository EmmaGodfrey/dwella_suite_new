import { defineStore } from 'pinia';

import language from '~/data/language.json';
import lang from '~/types/language';

export const useLanguageStore = defineStore('language', () => {
  const data = ref<lang[]>(language.langs);
  return {
    data,
  };
});
