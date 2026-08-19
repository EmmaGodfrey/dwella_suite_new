<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="profile-post">
        <div class="post-header">
          <div class="media">
            <img class="img-thumbnail rounded-circle me-3" src="/images/user/7.jpg" alt="Generic placeholder image" />
            <div class="media-body align-self-center" id="first-post-tour">
              <nuxt-link to="/pages/social_app">
                <h5 class="user-name">Emay Walter</h5>
              </nuxt-link>
              <h6>2 Hours ago</h6>
            </div>
          </div>
          <div class="post-setting"><i class="fa fa-ellipsis-h"></i></div>
        </div>
        <div class="post-body">
          <div class="img-container">
            <div class="my-gallery" id="aniimated-thumbnials">
              <div v-for="(src, index) in imgs" :key="index" @click="() => showImg(index)">
                <img :src="src.src" class="img-fluid rounded" />
              </div>
              <client-only> <vue-easy-lightbox :index="indexRef" :visible="visible" :imgs="imgs" @hide="handleHide"></vue-easy-lightbox></client-only>
            </div>
          </div>
          <div class="post-react mt-3">
            <ul>
              <li><img class="rounded-circle" src="/images/user/3.jpg" alt="" /></li>
              <li><img class="rounded-circle" src="/images/user/5.png" alt="" /></li>
              <li><img class="rounded-circle" src="/images/user/1.jpg" alt="" /></li>
            </ul>
            <h6>+20 people react this post</h6>
          </div>
          <p>
            Comfort is very important to me. I think people live better in big houses and in big clothes. Design and style should work toward making you look good and feel good without a lot of effort
            so you can get on with the things that matter. My shows are about the complete woman who swallows it all. Its a question of survival. Those fashion designers are just crazy; but arent we
            all? You can only go forward by making mistakes.
          </p>
          <ul class="post-comment">
            <li>
              <label
                ><a href="#">
                  <Icon name="ic:baseline-favorite-border" class=" " size="30" />
                  &nbsp;&nbsp;Like

                  <CommenNumberAnimations data="407" /> </a
              ></label>
            </li>
            <li>
              <label
                ><a href="#">
                  <Icon name="lucide:message-square" class=" " size="30" />&nbsp;&nbsp;Comment

                  <CommenNumberAnimations data="302" /> </a
              ></label>
            </li>
            <li>
              <label
                ><a href="#">
                  <Icon name="fluent:share-ios-24-filled" class="" size="20" />
                  &nbsp;&nbsp;share

                  <CommenNumberAnimations data="180" /> </a
              ></label>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
interface images {
  src: string;
}
interface single {
  image: string;
}

const visible = ref<boolean>(false);
const indexRef = ref<number>(0);
const imgs = ref<images[]>([{ src: '/images/user-profile/post4.jpg' }]);
const img = ref<single[]>([{ image: 'user-profile/post4.jpg' }]);

function showImg(index: number) {
  indexRef.value = index;
  visible.value = true;
}
function handleHide() {
  visible.value = false;
}
</script>
