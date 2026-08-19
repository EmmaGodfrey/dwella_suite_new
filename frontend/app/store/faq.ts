import { defineStore } from 'pinia';

import faq from '~/data/faq.json';
import faqarticles from '~/types/faqarticles';
import faqfeatured from '~/types/faqfeatured';

export const useFaqStore = defineStore('faq', () => {
  const data = ref<faqfeatured[]>(faq.featured);
  const list = ref<faqarticles[]>(faq.articles);
  const articles = ref<faqarticles[]>(faq.articles1);
  const articles1 = ref<faqarticles[]>(faq.articles2);
  return {
    data,
    list,
    articles,
    articles1,
  };
});
