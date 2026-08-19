<template>
  <div class="col-xl-9 xl-60 box-col-60">
    <div class="blog-single">
      <LearningCourseBlogBox />
      <div class="card comment-box">
        <div class="card-body">
          <h4>Comment</h4>
          <ul>
            <li>
              <div class="media align-self-center">
                <img class="align-self-center" :src="getImages('blog/comment.jpg')" alt="Generic placeholder image" />
                <div class="media-body">
                  <div class="row">
                    <div class="col-md-4 xl-100">
                      <nuxt-link to="/users/profile">
                        <h6 class="mt-0">Jolio Mark<span> ( Designer )</span></h6>
                      </nuxt-link>
                    </div>
                    <div class="col-md-8 xl-100">
                      <ul class="comment-social learning-comment">
                        <li class="digits"><i class="icofont icofont-thumbs-up"></i>02 Hits</li>
                        <li class="digits"><i class="icofont icofont-ui-chat"></i>598 Comments</li>
                      </ul>
                    </div>
                  </div>
                  <p>
                    There are many variations of passages of Lorem Ipsum available, but the majority have suffered alteration in some form, by injected humour, or randomised words which don't look
                    even slightly believable. If you are going to use a passage of Lorem Ipsum, you need to be sure there isn't anything embarrassing hidden in the middle of text.
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
                            <h6 class="mt-0">Jolio Mark<span> ( Designer )</span></h6>
                          </nuxt-link>
                        </div>
                      </div>
                      <p>
                        The best thing is location and drive through the forest. The resort is 35km from Ramnagar. The gardens are well kept and maintained. Its a good place for relaxation away from
                        the city noise. The staff is very friendly and overall we had a really good & fun time, thanks to staff member - Bhairav, Rajat, Gunanand, Lokesh & everyone else. And also we
                        went for an adventurous night safari and saw barking deers, tuskar elephant.
                      </p>
                    </div>
                  </div>
                </li>
              </ul>
            </li>
            <li>
              <div class="media">
                <img class="align-self-center" :src="getImages('blog/4.jpg')" alt="Generic placeholder image" />
                <div class="media-body">
                  <div class="row">
                    <div class="col-md-4 xl-100">
                      <nuxt-link to="/users/profile">
                        <h6 class="mt-0">Jolio Mark<span> ( Designer )</span></h6>
                      </nuxt-link>
                    </div>
                    <div class="col-md-8 xl-100">
                      <ul class="comment-social learning-comment">
                        <li class="digits"><i class="icofont icofont-thumbs-up"></i>02 Hits</li>
                        <li class="digits"><i class="icofont icofont-ui-chat"></i>598 Comments</li>
                      </ul>
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
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
