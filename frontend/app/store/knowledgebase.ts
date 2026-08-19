import { computed } from 'vue';

import { defineStore } from 'pinia';

import knowledgebase from '~/data/knowledgebase.json';
import categoryknow from '~/types/categoryknow';
import featured from '~/types/featuredknow';

export const useKnowledgebaseStore = defineStore('knowledgebase', () => {
  const cours = ref<featured[]>(knowledgebase.featured);
  const category = ref<categoryknow[]>(knowledgebase.category);

  return {
    cours,
    category,
  };
});
