<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="profile-post" id="last-post-tour">
        <div class="post-header">
          <div class="media">
            <img class="img-thumbnail rounded-circle me-3" src="/images/user/7.jpg" alt="Generic placeholder image" />
            <div class="media-body align-self-center" id="last-post-tour">
              <nuxt-link to="/pages/social_app">
                <h5 class="user-name">Emay Walter</h5>
              </nuxt-link>
              <h6>5 Hours ago</h6>
            </div>
          </div>
          <div class="post-setting"><i class="fa fa-ellipsis-h"></i></div>
        </div>
        <div class="post-body">
          <div class="img-container">
            <div class="row mt-4 pictures my-gallery" id="aniimated-thumbnials-2">
              <figure class="col-sm-6" itemprop="associatedMedia" v-for="(src, index) in imgs" :key="index" @click="() => showImg(index)">
                <img class="img-fluid rounded" :src="'/images/user-profile/' + src.src" itemprop="thumbnail" alt="Image description" />
              </figure>
            </div>
            <client-only> <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="lightBoxImages" @hide="handleHide"></vue-easy-lightbox></client-only>
          </div>
          <div class="post-react">
            <ul>
              <li><img class="rounded-circle" src="/images/user/3.jpg" alt="" /></li>
              <li><img class="rounded-circle" src="/images/user/5.png" alt="" /></li>
              <li><img class="rounded-circle" src="/images/user/1.jpg" alt="" /></li>
            </ul>
            <h6>+25 people react this post</h6>
          </div>
          <p>
            Success isn't about the end result, it's about what you learn along the way. Confidence. If you have it, you can make anything look good. Grunge is a hippied romantic version of punk. I'm
            an accomplice to helping women get what they want. Clothes can transform your mood and confidence. I think it's an old fashioned notion that fashion needs to be exclusive to be
            fashionable.
          </p>
          <ul class="post-comment">
            <li>
              <label
                ><a href="#">
                  <Icon name="ic:baseline-favorite-border" class=" " size="30" />
                  &nbsp;&nbsp;Like

                  <CommenNumberAnimations data="520" /> </a
              ></label>
            </li>
            <li>
              <label
                ><a href="#">
                  <Icon name="lucide:message-square" class=" " size="30" />&nbsp;&nbsp;Comment

                  <CommenNumberAnimations data="85" /> </a
              ></label>
            </li>
            <li>
              <label
                ><a href="#">
                  <Icon name="fluent:share-ios-24-filled" class="" size="20" />
                  &nbsp;&nbsp;share

                  <CommenNumberAnimations data="30" /> </a
              ></label>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
  <UserProfilePost2 />
</template>
<script lang="ts" setup>
interface images {
  src: string;
}
interface single {
  image: string;
}
interface LightBoxImage {
  src: string;
  caption?: string;
  title?: string;
}
const lightBoxImages = ref<LightBoxImage[]>([]);
const visible = ref<boolean>(false);

const indexRef = ref<number>(0);
const imgs = ref<images[]>([{ src: '/post2.jpg' }, { src: '/post3.jpg' }]);
const img = ref<single[]>([{ image: '/post2.jpg' }, { image: '/post3.jpg' }]);

function showImg(index: number) {
  indexRef.value = index;
  visible.value = true;
}
function handleHide() {
  visible.value = false;
}
onMounted(() => {
  imgs.value.forEach(item => {
    lightBoxImages.value.push({ src: '/images/user-profile/' + item.src });
  });
});
</script>
