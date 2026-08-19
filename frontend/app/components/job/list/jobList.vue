<template>
  <div class="col-xl-9 xl-60 box-col-60">
    <div class="card" v-for="(job, index) in jobs" :key="index" :class="{ 'ribbon-vertical-left-wrapper': job.priority == 1 || job.priority == 7 }">
      <div v-if="job.priority == 1" class="ribbon ribbon-bookmark ribbon-vertical-left ribbon-primary"><i class="icofont icofont-globe-alt"></i></div>
      <div v-if="job.priority == 7" class="ribbon ribbon-bookmark ribbon-vertical-left ribbon-secondary"><i class="icofont icofont-award"></i></div>
      <div class="job-search">
        <div class="card-body">
          <div class="media">
            <img class="img-40 img-fluid m-r-20" :src="getImages(job.image)" alt="" />
            <div class="media-body">
              <h6 class="f-w-600">
                <nuxt-link :to="`/job/details/${job.id}`">{{ job.title }}</nuxt-link
                ><span class="pull-right" v-if="job.date" v-text="job.date"></span>
                <span class="badge badge-primary pull-right" v-else>New</span>
              </h6>
              <p>
                {{ job.company }} <span>{{ job.city }}, {{ job.country }} </span> <span v-html="stars(job.stars)"></span>
              </p>
            </div>
          </div>
          <p v-text="job.description"></p>
        </div>
      </div>
    </div>

    <div class="job-pagination">
      <nav aria-label="Page navigation example">
        <ul class="pagination pagination-primary">
          <li class="page-item disabled"><a class="page-link" href="javascript:void(0)">Previous</a></li>
          <li class="page-item active"><a class="page-link" href="javascript:void(0)">1</a></li>
          <li class="page-item"><a class="page-link" href="javascript:void(0)">2</a></li>
          <li class="page-item"><a class="page-link" href="javascript:void(0)">3</a></li>
          <li class="page-item"><a class="page-link" href="javascript:void(0)">Next</a></li>
        </ul>
      </nav>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useJobStore } from '~/store/job';

const store = useJobStore();
const { jobs } = storeToRefs(store);
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
