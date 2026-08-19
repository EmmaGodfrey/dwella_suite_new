<template>
  <div class="col-xl-9 xl-60 box-col-60">
    <div class="card">
      <div class="job-search">
        <div class="card-body pb-0">
          <div class="media">
            <img class="img-40 img-fluid m-r-20" :src="getImages(jobs.image)" alt="" />
            <div class="media-body">
              <h5 class="f-w-700 mb-0">
                <nuxt-link :to="`/job/details/${jobs.id}`">{{ jobs.title }}</nuxt-link>
              </h5>
              <p>
                {{ jobs.company }} <span>{{ jobs.city }}, {{ jobs.country }} </span> <span v-html="stars(jobs.stars)"></span>
              </p>
              <button class="btn btn-primary job-apply-btn" type="button">
                <span><i class="fa fa-check text-white"></i></span> Save this job
              </button>
            </div>
          </div>
          <JobApplyPersonalDetails />
        </div>
        <div class="card-footer">
          <button class="btn btn-primary me-1" type="submit">Submit</button>
          <input class="btn btn-light" type="reset" value="Cancel" />
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useRoute } from 'vue-router';

import { getImages } from '~/composables/commen/imgMixin';
import { useJobStore } from '~/store/job';

const store = useJobStore();
const { job } = storeToRefs(store);
const route = useRoute();

const jobs = computed(
  () =>
    job.value.find(job => parseInt(route.params.id as string) === job.id) ?? {
      id: 0,
      image: '',
      title: 'Job not found',
      company: '',
      city: '',
      country: '',
      stars: 0,
      description: '',
      resp: [],
      reqs: [],
      skills: [],
    },
);
function stars(count: number) {
  var stars = '';

  for (var i = 0; i < 5; i++) {
    if (count > i) {
      stars = stars + '<i class="fa fa-star font-warning"></i>';
    } else {
      stars = stars + '<i class="fa fa-star-o font-warning"></i>';
    }
  }

  return stars;
}
</script>
