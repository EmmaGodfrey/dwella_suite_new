import { defineStore } from 'pinia';

import book from '~/data/bookmark.json';
import project from '~/data/project.json';
import user from '~/data/user.json';
import bookmark from '~/types/bookmark';
import projectlist from '~/types/projectlist';

interface item {
  icon: string;
  title: string;
  desc: string;
}
interface items {
  img: string;
  name: string;
  frd: string;
}
interface img {
  img: string;
}
export const useProjectStore = defineStore('project', () => {
  const data = ref<projectlist[]>(project.all);
  const doing = ref<projectlist[]>(project.Doing);
  const done = ref<projectlist[]>(project.done);
  const about = ref<item[]>(user.data);
  const follower = ref<items[]>(user.follower);
  const following = ref<items[]>(user.following);
  const latest = ref<img[]>(user.latest);
  const friend = ref<img[]>(user.friend);
  const bookmark = ref<bookmark[]>(book.data);
  const favourite = ref<bookmark[]>([]);
  const activeclass = ref<string>('pills_created');

  function say(item: string) {
    activeclass.value = item;
  }
  function getActive(itemId: number) {
    const objIndex = favourite.value.findIndex((obj: bookmark) => obj.id === itemId);
    if (objIndex > -1) {
      return true;
    } else {
      return false;
    }
  }
  return {
    data,
    doing,
    done,
    about,
    getActive,
    bookmark,
    activeclass,
    favourite,
    follower,
    say,
    following,
    friend,
    latest,
  };
});
