import { defineStore } from 'pinia';

import filemaneger from '~/data/filemaneger.json';

interface folder {
  id: number;
  name: string;
  icon: string;
  hour: string;
  file: string;
}
interface file {
  id: number;
  icon: string;
  name: string;
  day: string;
}
interface side {
  icon: string;
  title: string;
  class: string;
}
interface qui {
  icon: string;
  title: string;
}
interface pri {
  img: string;
  version: string;
  fre: string;
  space: string;
}

export const useFilemanegerStore = defineStore('filemaneger', () => {
  const folders = ref<folder[]>(filemaneger.folders);
  const files = ref<file[]>(filemaneger.files);
  const sidebar = ref<side[]>(filemaneger.sidebar);
  const quick = ref<qui[]>(filemaneger.quick);
  const pricing = ref<pri[]>(filemaneger.pricing);
  return {
    folders,
    files,
    sidebar,
    quick,
    pricing,
  };
});
