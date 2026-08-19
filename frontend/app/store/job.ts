import { defineStore } from 'pinia';

import item from '~/data/job.json';
import jobdetails from '~/types/jobdetails';
import joblist from '~/types/joblist';

export const useJobStore = defineStore('job', () => {
  const job = ref<jobdetails[]>(item.job);
  const jobs = ref<jobdetails[]>(item.jobs);
  const data = ref<joblist[]>(item.data);
  return {
    data,
    job,
    jobs,
  };
});
