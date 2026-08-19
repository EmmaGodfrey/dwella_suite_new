<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>IMAGE GALLERY</h5>
      </div>
      <div class="card-body">
        <div class="my-gallery gallery row" itemscope>
          <figure v-for="(src, index) in masonryItems" :key="index" class="col-xl-3 col-md-4 col-sm-6 xl-33 box-col-33" @click="() => showImg(index)">
            <a itemprop="contentUrl" data-size="1600x950">
              <img :src="getImgUrl(src.image)" alt="Image description" class="img-thumbnail" />
            </a>
            <div class="caption"></div>
          </figure>
        </div>
      </div>
      <client-only> <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="lightBoxImages" @hide="handleHide"> </vue-easy-lightbox></client-only>
    </div>
  </div>
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
const { image } = storeToRefs(store);
const masonryItems = image.value;
onMounted(() => {
  masonryItems.forEach(item => {
    lightBoxImages.value.push({ src: '/images/' + item.image });
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
