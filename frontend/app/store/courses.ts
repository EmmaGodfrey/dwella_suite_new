import { computed } from 'vue';

import { defineStore } from 'pinia';

import item from '~/data/courses.json';
import learning from '~/types/learning';

export const useCoursesStore = defineStore('courses', () => {
  const cours = ref<learning[]>(item.courses);

  const specialCourses = computed(() => {
    return cours.value.filter(course => {
      if (course.special === 1) return course;
    });
  });
  const normalCourses = computed(() => {
    return cours.value.filter(course => {
      if (course.special === 0) return course;
    });
  });
  return {
    cours,
    normalCourses,
    specialCourses,
  };
});
