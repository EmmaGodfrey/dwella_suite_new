<template>
  <div class="col-xl-9 xl-60 box-col-60">
    <div class="card">
      <div class="job-search">
        <div class="card-body">
          <div class="media align-items-center">
            <img class="img-40 img-fluid m-r-20" :src="getImages(jobs.image)" alt="" />
            <div class="media-body">
              <h5 class="f-w-700 mb-0">
                <nuxt-link :to="`/job/details/${jobs.id}`">{{ jobs.title }}</nuxt-link>
              </h5>
              <p>
                {{ jobs.company }} <span>{{ jobs.city }}, {{ jobs.country }} </span> <span v-html="stars(jobs.stars)"></span>
              </p>
              <nuxt-link :to="`/job/apply/${jobs.id}`" class="btn btn-primary btn-sm job-apply-btn">Apply for this job</nuxt-link>
            </div>
          </div>
          <div class="job-description">
            <h6>Job Description</h6>
            <p class="text-start" v-html="jobs.description"></p>
          </div>
          <div class="job-description">
            <h6>Qualifications</h6>
            <ul>
              <li v-for="(r, index) in jobs.resp" :key="index" v-text="r.title"></li>
            </ul>
          </div>
          <div class="job-description">
            <h6>Agency experience</h6>
            <ul>
              <li v-for="(rq, index) in jobs.reqs" :key="index" v-text="rq.title"></li>
            </ul>
          </div>
          <div class="job-description">
            <h6>Perks</h6>
            <ul>
              <li v-for="(ski, index) in jobs.skills" :key="index" v-text="ski.title"></li>
            </ul>
          </div>
          <div class="job-description">
            <button class="btn btn-primary me-2" type="button">
              <span><i class="fa fa-check"></i></span> Save this job
            </button>
            <button class="btn btn-primary" type="button">
              <span><i class="fa fa-share-alt"></i></span> Share
            </button>
          </div>
        </div>
      </div>
    </div>
    <JobDetailsSimilarJobs />
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
