<template>
  <div class="col-xl-9 box-col-9">
    <div class="row">
      <div class="col-xl-12 col-sm-6" v-for="(courses, index) in specialCourses" :key="'special' + index">
        <div class="card">
          <div class="blog-box blog-list row">
            <div class="col-xl-5 col-12"><img class="img-fluid sm-100-w" :src="getImages(courses.image ?? '')" alt="" /></div>
            <div class="col-xl-7 col-12">
              <div class="blog-details">
                <div class="blog-date"><span v-text="courses.dd"></span> {{ courses.mm }} {{ courses.yy }}</div>
                <nuxt-link to="/learning/details/1">
                  <h6 v-text="courses.title"></h6>
                </nuxt-link>
                <div class="blog-bottom-content">
                  <ul class="blog-social">
                    <li v-text="' by: ' + courses.author"></li>
                    <li class="digits" v-text="courses.hits + ' Hits'"></li>
                  </ul>
                  <hr />
                  <p class="mt-0" v-text="courses.descr"></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-xl-4 col-sm-6 box-col-33" v-for="(course, index) in normalCourses" :key="'normal' + index">
        <div class="card">
          <div class="product-box learning-box">
            <div class="product-img">
              <img class="img-fluid top-radius-blog" :src="getImages(course.image ?? '')" alt="" />
              <div class="product-hover">
                <ul>
                  <li>
                    <nuxt-link to="/learning/details/1"><i class="icon-link"></i> </nuxt-link>
                  </li>
                  <li>
                    <nuxt-link to="/learning/details/1"><i class="icon-import"></i></nuxt-link>
                  </li>
                </ul>
              </div>
            </div>
            <div class="details-main">
              <nuxt-link to="/learning/details/1">
                <div class="bottom-details">
                  <h6 v-text="course.title"></h6>
                </div>
              </nuxt-link>
              <p>{{ course.descr }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useCoursesStore } from '~/store/courses';

const store = useCoursesStore();
const { specialCourses, normalCourses } = storeToRefs(store);
</script>
