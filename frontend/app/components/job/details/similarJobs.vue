<template>
  <div class="header-faq">
    <h5 class="mb-0 f-w-600">Similar jobs</h5>
  </div>
  <div class="row">
    <div class="col-xl-6 xl-100 box-col-12" v-for="(job, index) in data" :key="index">
      <div class="card">
        <div class="job-search">
          <div class="card-body">
            <div class="media align-items-center">
              <img class="img-40 img-fluid m-r-20" :src="getImages(job.image)" alt="" />
              <div class="media-body">
                <h6 class="f-w-600">
                  <a href="javascript:void(0)">{{ job.title }}</a
                  ><span class="pull-right" v-if="job.date" v-text="job.date"></span>
                  <span class="badge badge-primary pull-right" v-else>New</span>
                </h6>
                <p>
                  {{ job.company }} <span>{{ job.city }}, {{ job.country }} </span> <span v-html="stars(job.stars)"></span>
                </p>
              </div>
            </div>
            <p>{{ job.description }}</p>
          </div>
        </div>
      </div>
    </div>
    <div class="col-xl-12">
      <div class="card">
        <div class="job-search">
          <div class="card-body">
            <div class="media align-items-center">
              <img class="img-40 img-fluid m-r-20" :src="getImages('job-search/3.jpg')" alt="" />
              <div class="media-body">
                <h6 class="f-w-600"><a href="javascript:void(0)">Senior UX designer</a><span class="pull-right">5 days ago</span></h6>
                <p>Sutherland <span>Lelystad, Netherlands </span></p>
                <ul class="rating">
                  <li><i class="fa fa-star font-warning"></i></li>
                  <li><i class="fa fa-star font-warning"></i></li>
                  <li><i class="fa fa-star font-warning"></i></li>
                  <li><i class="fa fa-star font-warning"></i></li>
                  <li><i class="fa fa-star-o font-warning"></i></li>
                </ul>
              </div>
            </div>
            <p>
              Woody equal ask saw sir weeks aware decay. Entrance prospect removing we packages strictly is no smallest he. For hopes may chief get hours day rooms. Oh no turned behind polite piqued
              enough at. Forbade few through inquiry blushes you. Cousin no itself eldest it in dinner latter missed no.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useJobStore } from '~/store/job';

const store = useJobStore();
const { data } = storeToRefs(store);

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
