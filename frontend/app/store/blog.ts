import { defineStore } from 'pinia';

import blog from '~/data/blog.json';
import blogdetail from '~/types/blogdetail';
import bloglist from '~/types/bloglist';
import blogsingle from '~/types/blogsingle';

export const useBlogStore = defineStore('blog', () => {
  const data = ref<blogdetail[]>(blog.details);
  const list = ref<bloglist[]>(blog.list);
  const single = ref<blogsingle[]>(blog.single);
  return {
    data,
    list,
    single,
  };
});
