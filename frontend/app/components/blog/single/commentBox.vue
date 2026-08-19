<template>
  <div class="card comment-box">
    <div class="card-body">
      <h4>Comment</h4>
      <ul>
        <li>
          <div class="media align-self-center">
            <img class="align-self-center" :src="getImages('blog/comment.jpg')" alt="Generic placeholder image" />
            <div class="media-body">
              <div class="row">
                <div class="col-md-4">
                  <nuxt-link to="/users/profile">
                    <h6 class="mt-0">Jolio Mark<span> ( Developer )</span></h6>
                  </nuxt-link>
                </div>
                <div class="col-md-8">
                  <ul class="comment-social">
                    <li><i class="icofont icofont-thumbs-up"></i>04 Hits</li>
                    <li><i class="icofont icofont-ui-chat"></i>598 Comments</li>
                  </ul>
                </div>
              </div>
              <p>
                The best thing is location and drive through the forest. The resort is 35km from Ramnagar. The gardens are well kept and maintained. Its a good place for relaxation away from the city
                noise. The staff is very friendly and overall we had a really good & fun time, thanks to staff member - Bhairav, Rajat, Gunanand, Lokesh & everyone else. And also we went for an
                adventurous night safari and saw barking deers, tuskar elephant.
              </p>
            </div>
          </div>
        </li>
        <li>
          <ul>
            <li>
              <div class="media">
                <img class="align-self-center" :src="getImages('blog/9.jpg')" alt="Generic placeholder image" />
                <div class="media-body">
                  <div class="row">
                    <div class="col-xl-12">
                      <nuxt-link to="/users/profile">
                        <h6 class="mt-0">Jhon Deo<span> ( Designer )</span></h6>
                      </nuxt-link>
                    </div>
                  </div>
                  <p>
                    Clean resort with maintained garden but rooms are average Lack of communication between the staff members. Receptionsit full of attitude. Arrogant staff. Except good view there is
                    nothing great in this property.Resort is 35 kms away from Ramnagar Town.
                  </p>
                </div>
              </div>
            </li>
          </ul>
        </li>
        <li v-for="(item, index) in comment" :key="index">
          <div class="media">
            <img class="align-self-center" :src="getImages(item.imge)" alt="Generic placeholder image" />
            <div class="media-body">
              <div class="row">
                <div class="col-md-4">
                  <nuxt-link to="/users/profile">
                    <h6 class="mt-0">
                      {{ item.name }}<span> ( {{ item.dep }} )</span>
                    </h6>
                  </nuxt-link>
                </div>
                <div class="col-md-8">
                  <ul class="comment-social">
                    <li><i class="icofont icofont-thumbs-up"></i>{{ item.hits }} Hits</li>
                    <li><i class="icofont icofont-ui-chat"></i>{{ item.comments }} Comments</li>
                  </ul>
                </div>
              </div>
              <p>{{ item.desc }}</p>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useBlogStore } from '~/store/blog';

const store = useBlogStore();
const { single } = storeToRefs(store);
const comment = single.value;
</script>
