<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>MASONRY GALLERY WITH DESCRIPTION</h5>
      </div>
      <div class="card-body">
        <MasonryWall class="my-gallery row grid gallery-with-description" id="aniimated-thumbnials" :items="masonry" :padding="5" :column-width="300" :gap="5">
          <template #default="{ item }" class="grid-item col-xl-3 col-sm-6">
            <figure @click="() => showImg(item.id!)">
              <a>
                <img :src="getImgUrl(item.image!)" class="img-fluid" />
                <div class="caption description">
                  <h4>{{ item.title }}</h4>
                  <p>{{ item.descr }}</p>
                </div>
              </a>
            </figure>
          </template>
        </MasonryWall>
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
const { imageArray } = storeToRefs(store);
const masonry = imageArray.value;
onMounted(() => {
  masonry.forEach(item => {
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
