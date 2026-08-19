<template>
  <ClientOnly>
    <div class="col-sm-12">
      <div class="header-faq">
        <h5 class="mb-0">knowledge articles by category</h5>
      </div>
      <div class="row browse">
        <div class="col-xl-4 xl-50 col-md-6" v-for="(item, index) in category" :key="index">
          <div class="browse-articles">
            <h6>
              <span> <Icon name="majesticons:archive-line" class="me-1" size="20" /> </span>{{ item.articles }}
            </h6>
            <ul>
              <li>
                <nuxt-link to="/knowledgebase/knowledge_detail">
                  <h5><Icon name="tabler:file-text" class="" size="20" /> {{ item.articles1 }}</h5>
                </nuxt-link>
              </li>
              <li>
                <nuxt-link to="/knowledgebase/knowledge_detail">
                  <h5><Icon name="tabler:file-text" class="" size="20" />{{ item.articles2 }}</h5>
                </nuxt-link>
              </li>
              <li>
                <nuxt-link to="/knowledgebase/knowledge_detail">
                  <h5><Icon name="tabler:file-text" class="" size="20" />{{ item.articles3 }}</h5>
                </nuxt-link>
              </li>
              <li>
                <nuxt-link to="/knowledgebase/knowledge_detail">
                  <h5><Icon name="tabler:file-text" class="" size="20" />{{ item.articles4 }}</h5>
                </nuxt-link>
              </li>
              <li>
                <a class="f-w-600 font-primary"
                  ><nuxt-link to="/knowledgebase/knowledge_detail">
                    <Icon name="iconamoon:arrow-right-1-bold" class="me-1" size="20" /> <span>See More ({{ item.see }})</span>
                  </nuxt-link></a
                >
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div></ClientOnly
  >
</template>
<script lang="ts" setup>
import { useKnowledgebaseStore } from '~/store/knowledgebase';

const store = useKnowledgebaseStore();
const { category } = storeToRefs(store);
</script>
