<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header">
        <h5>MASONRY GALLERY WITH DESCRIPTION</h5>
      </div>
      <div class="card-body">
        <MasonryWall class="my-gallery row grid gallery" :items="masonryItems" :padding="5" :column-width="300" :gap="5">
          <template #default="{ item }" class="col-md-3 col-sm-6 grid-item">
            <figure itemprop="associatedMedia" itemscope>
              <img :src="getImgUrl(item.image)" @click="() => showImg(item.id!)" alt="Image description" class="img-thumbnail" />
            </figure>
          </template>
        </MasonryWall>
        <client-only> <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="lightBoxImages" @hide="handleHide"> </vue-easy-lightbox></client-only>
      </div>
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
const { imags } = storeToRefs(store);
const masonryItems = imags.value;
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
