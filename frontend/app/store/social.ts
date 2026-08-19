import { defineStore } from 'pinia';

import social from '~/data/social.json';

interface friends {
  image: string;
  StatusClass: string;
  name: string;
  email: string;
}
interface activity {
  name: string;
  image: string;
}
interface post {
  id: number;
  name: string;
  msg: string;
  class: string;
  image: string;
  date: string;
}
interface addfriend {
  image: string;
  name: string;
}
interface item {
  title: string;
  title1: string;
  desc: string;
  desc1: string;
}
interface items {
  title: string;
  year: string;
  desc: string;
  title1: string;
  year1: string;
  desc1: string;
}

export const useSocialStore = defineStore('social', () => {
  const data = ref<friends[]>(social.friends);
  const activity = ref<activity[]>(social.activity);
  const post = ref<post[]>(social.post);
  const post1 = ref<post[]>(social.post1);
  const addfriend = ref<addfriend[]>(social.addfriend);
  const hobbies = ref<item[]>(social.hobbies);
  const education = ref<items[]>(social.education);
  return {
    data,
    activity,
    post,
    post1,
    addfriend,
    hobbies,
    education,
  };
});
