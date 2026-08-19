<template>
  <div class="col-lg-12 featured-tutorial">
    <div class="header-faq">
      <h5 class="mb-0">Featured Tutorials</h5>
    </div>
    <div class="row">
      <div class="col-xl-3 xl-50 col-sm-6 box-col-6" v-for="(item, index) in data" :key="index">
        <div class="card features-faq product-box">
          <div class="faq-image product-img">
            <img class="img-fluid" :src="getImages(item.imge)" alt="" />
            <div class="product-hover">
              <ul>
                <li>
                  <nuxt-link to="/knowledgebase/knowledge_detail"><i class="icon-link"></i></nuxt-link>
                </li>
                <li>
                  <nuxt-link to="/knowledgebase/knowledge_detail"><i class="icon-import"></i></nuxt-link>
                </li>
              </ul>
            </div>
          </div>
          <div class="card-body">
            <nuxt-link to="/knowledgebase/knowledge_detail">
              <h6>{{ item.title }}</h6>
            </nuxt-link>
            <p>{{ item.desc }}</p>
          </div>
          <div class="card-footer">
            <span>{{ item.date }}</span> <span class="pull-right" v-html="stars(item.star)"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useKnowledgebaseStore } from '~/store/knowledgebase';

const store = useKnowledgebaseStore();
const { cours } = storeToRefs(store);
const data = cours.value;

function stars(count: number) {
  var stars = '';

  for (var i = 0; i < 5; i++) {
    if (count > i) {
      stars = stars + '<i class="fa fa-star font-primary"></i>';
    } else {
      stars = stars + '<i class="fa fa-star-o font-primary"></i>';
    }
  }

  return stars;
}
</script>
