import { defineStore } from 'pinia';

import todo from '~/data/todo.json';

export const useTodoStore = defineStore('todo', () => {
  const data = ref(todo.data);
  function taskcomplete(item: number) {
    data.value.find(function (list) {
      if (list.id === item) {
        return (list.status = list.status === 'complete' ? 'incomplete' : 'complete');
      }
    });
  }
  function tododelete(index: number) {
    data.value.splice(index, 1);
  }

  function addtodo(item: string) {
    const todoIDs = data.value.map(element => element.id);
    const id = (todoIDs.length ? Math.max(...todoIDs) : 0) + 1;

    data.value.unshift({
      id: id,
      title: item,
      priority: 'Pending',
      date: '16 Jan',
      badgeClass: 'badge-light-danger',
      delete: false,
      status: 'incomplete',
    });
  }

  return {
    data,
    taskcomplete,
    tododelete,
    addtodo,
  };
});
