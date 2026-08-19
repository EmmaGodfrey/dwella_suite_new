<template>
  <div class="info-block m-t-30">
    <p class="pb-4 col-sm-12 digits">About 12,120 results (0.50 seconds)</p>
    <div class="my-gallery row gallery-with-description" id="aniimated-thumbnials" itemscope>
      <figure v-for="(src, index) in search" :key="index" class="col-xl-3 col-sm-6 box-col-33" @click="() => showImg(index)">
        <a>
          <img :src="getImgUrl(src.image ?? '')" alt="Image description" class="img-fluid" />
          <div class="caption description">
            <h4>{{ src.title }}</h4>
            <p>{{ src.descr }}</p>
          </div>
        </a>
      </figure>
    </div>
    <client-only>
      <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="lightBoxImages" @hide="handleHide"> </vue-easy-lightbox>
    </client-only>
  </div>
  <SearchPaginationView />
</template>
<script lang="ts" setup>
import { useMasonryStore } from '~/store/masonry';

interface LightBoxImage {
  src: string;
  caption?: string;
  title?: string;
}
const lightBoxImages = ref<LightBoxImage[]>([]);

const visible = ref<boolean>(false);
const indexRef = ref<number>(0);
const store = useMasonryStore();
const { search } = storeToRefs(store);

onMounted(() => {
  search.value.forEach(item => {
    lightBoxImages.value.push({ src: '/images/' + item.image, title: item.title });
  });
});
function showImg(index: number) {
  indexRef.value = index;
  visible.value = true;
}
function handleHide() {
  visible.value = false;
}

function getImgUrl(path: string) {
  return '/images/' + path;
}
</script>
