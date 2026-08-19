<template>
  <div class="col-lg-12 faq-articles">
    <div class="header-faq">
      <h5 class="mb-0">Latest articles and videos</h5>
    </div>
    <div class="row">
      <div class="col-xl-4 col-md-6">
        <div class="row">
          <div class="col-sm-12" v-for="(item, index) in list" :key="index">
            <div class="card">
              <div class="card-body">
                <div class="media">
                  <Icon :name="item.icon" class="m-r-30" size="25" />
                  <div class="media-body">
                    <h6 class="f-w-600">{{ item.title }}</h6>
                    <p>{{ item.desc }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-4 col-md-6">
        <div class="row">
          <div class="col-sm-12" v-for="(item, index) in articles" :key="index">
            <div class="card">
              <div class="card-body">
                <div class="media">
                  <Icon :name="item.icon" class="m-r-30" size="25" />
                  <div class="media-body">
                    <h6 class="f-w-600">{{ item.title }}</h6>
                    <p>{{ item.desc }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-xl-4">
        <div class="row">
          <div class="col-xl-12 col-md-6" v-for="(item, index) in articles1" :key="index">
            <div class="card">
              <div class="card-body">
                <div class="media">
                  <Icon :name="item.icon" class="m-r-30" size="25" />
                  <div class="media-body">
                    <h6 class="f-w-600">{{ item.title }}</h6>
                    <p>{{ item.desc }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useFaqStore } from '~/store/faq';

const store = useFaqStore();
const { list, articles, articles1 } = storeToRefs(store);
</script>
