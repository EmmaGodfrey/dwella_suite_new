<template>
  <div class="col-xl-3 col-lg-12 xl-35">
    <div class="default-according style-1 faq-accordion job-accordion">
      <div class="row">
        <div class="col-xl-12">
          <div class="card">
            <div class="card-header">
              <h5 class="p-0">
                <button
                  class="btn btn-link ps-0"
                  data-bs-toggle="collapse"
                  data-bs-target="#collapseExample"
                  :aria-expanded="isActive ? 'true' : 'false'"
                  :class="[isActive ? 'active' : '']"
                  v-on:click="toggle"
                >
                  About Me
                </button>
              </h5>
            </div>
            <div :class="[isActive ? 'block' : ' show']" v-show="isActive">
              <div class="card-body post-about">
                <ul>
                  <li v-for="(item, index) in data" :key="index">
                    <div class="icon">
                      <Icon :name="item.icon" class="facebook" size="30" />
                    </div>
                    <div>
                      <h5>{{ item.title }}</h5>
                      <p>{{ item.desc }}</p>
                    </div>
                  </li>
                </ul>
                <div class="social-network theme-form">
                  <span class="f-w-600">Social Networks</span>
                  <a class="btn social-btn btn-fb mb-2 text-center" href="https://www.facebook.com/" target="_blank"><i class="fa fa-facebook m-r-5"></i>Facebook</a>
                  <a class="btn social-btn btn-twitter mb-2 text-center" href="https://twitter.com/" target="_blank"><i class="fa fa-twitter m-r-5"></i>Twitter</a>
                  <a class="btn social-btn btn-google text-center" href="https://dribbble.com/" target="_blank"><i class="fa fa-dribbble m-r-5"></i>Dribbble</a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <CommenFollowersView />
        <CommenFollowingView />
        <CommenLatestPhotos />
        <CommenFriendsView />
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const store = useProjectStore();
const { about } = storeToRefs(store);
const data = about.value;
const isActive = ref<boolean>(true);
function toggle() {
  isActive.value = !isActive.value;
}
</script>
