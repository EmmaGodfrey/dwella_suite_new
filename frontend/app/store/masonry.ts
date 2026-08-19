import { defineStore } from 'pinia';

import masonry from '~/data/masonry.json';

interface photo {
  id?: number;
  title?: string;
  descr?: string;
  image?: string;
}
interface aos {
  image: string;
  animation: string;
}
interface image {
  id?: number;
  image: string;
}

export const useMasonryStore = defineStore('masonry', () => {
  const data = ref<photo[]>(masonry.photo);
  const search = ref<photo[]>(masonry.search);
  const aos = ref<aos[]>(masonry.aos);
  const image = ref<image[]>(masonry.image);
  const imgs = ref<photo[]>(masonry.imgs);
  const imags = ref<image[]>(masonry.imags);
  const imageArray = ref<photo[]>(masonry.imagearray);
  const hover = ref<image[]>(masonry.hover);
  return {
    data,
    search,
    aos,
    image,
    imgs,
    imags,
    imageArray,
    hover,
  };
});
