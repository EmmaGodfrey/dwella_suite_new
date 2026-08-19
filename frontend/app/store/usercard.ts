import { defineStore } from 'pinia';

import user from '~/data/user.json';
import userCard from '~/types/user';

export const useUserStore = defineStore('user', () => {
  const data = ref<userCard[]>(user.data1);

  return {
    data,
  };
});
