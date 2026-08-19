<template>
  <div class="card">
    <div class="card-header pb-0">
      <h5>AOS Example animation</h5>
    </div>
    <div class="card-body">
      <MasonryWall class="row gallery grid my-gallery" :items="masonryItems" :padding="5" :column-width="300" :gap="5">
        <template #default="{ item }" class="grid-item col-sm-4 col-md-3">
          <figure data-aos="fade-down">
            <aos-vue :animation="item.animation">
              <a @click="() => showImg(masonryItems.indexOf(item))">
                <img :src="getImages(item.image)" alt="Image description" class="img-thumbnail" />
              </a>
            </aos-vue>
          </figure>
        </template>
      </MasonryWall>

      <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="lightBoxImages" @hide="handleHide"> </vue-easy-lightbox>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useMasonryStore } from '~/store/masonry';

const lightBoxImages = ref<object[]>([]);
const indexRef = ref<number>(0);
const visible = ref<boolean>(false);
const store = useMasonryStore();
const { aos } = storeToRefs(store);
const masonryItems = aos.value;
onMounted(() => {
  masonryItems.forEach(item => {
    lightBoxImages.value.push({ src: '/images/' + item.image });
  });
});
function showImg(index: number) {
  masonryItems.forEach(item => {
    lightBoxImages.value.push({ src: '/images/' + item.image });
  });
  indexRef.value = index;
  visible.value = true;
}
function handleHide() {
  visible.value = false;
}
</script>
