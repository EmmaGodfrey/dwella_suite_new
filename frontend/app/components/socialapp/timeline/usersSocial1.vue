<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-body">
        <div class="new-users-social">
          <div class="media align-items-start">
            <img class="rounded-circle image-radius m-r-15" :src="getImages('user/1.jpg')" alt="" />
            <div class="media-body">
              <h6 class="mb-0 f-w-700">ELANA</h6>
              <p>January, 12,2023</p>
            </div>
            <span class="pull-right mt-0">
              <Icon name="akar-icons:more-vertical-fill" class="" size="20" />
            </span>
          </div>
        </div>
        <img class="img-fluid" alt="" :src="getImages('social-app/timeline-2.png')" />
        <div class="timeline-content">
          <p class="mb-0">
            I've always thought of the T-shirt as the Alpha of the fashion alphabet. My breakfast is very important. Everything I do is a matter of heart, body and soul. The only way to do something
            in depth is to work hard.
          </p>
          <div class="like-content">
            <span><i class="fa fa-heart font-danger"></i></span
            ><span class="pull-right comment-number"
              ><span>20 </span><span><i class="fa fa-share-alt me-0"></i></span></span
            ><span class="pull-right comment-number"
              ><span>10 </span><span><i class="fa fa-comments-o"></i></span
            ></span>
          </div>
          <div class="social-chat">
            <div :class="item.class" v-for="(item, index) in post" :key="index">
              <div class="media align-items-start">
                <img class="img-50 img-fluid m-r-20 rounded-circle" alt="" :src="getImages(item.image)" />
                <div class="media-body">
                  <span class="f-w-600"
                    >{{ item.name }} <span>{{ item.date }} <i class="fa fa-reply font-primary"></i></span
                  ></span>
                  <p class="mb-0">{{ item.msg }}</p>
                </div>
              </div>
            </div>
            <div class="text-center"><a class="f-w-600" href="javascript:void(0)">More Commnets</a></div>
          </div>
          <div class="comments-box">
            <div class="d-flex align-items-center">
              <img class="img-50 img-fluid m-r-20 rounded-circle" alt="" :src="getImages('user/1.jpg')" />
              <div class="flex-grow-1">
                <div class="input-group text-box">
                  <input class="form-control input-txt-bx" type="text" name="message-to-send" placeholder="Post Your commnets" />
                  <div class="input-group-text"><img alt="" :src="getImages('smiley.png')" /></div>
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
import { getImages } from '~/composables/commen/imgMixin';
import { useSocialStore } from '~/store/social';

const store = useSocialStore();
const { post1 } = storeToRefs(store);
const post = post1.value;
</script>
