<template>
  <div class="card-body">
    <section class="cd-container" id="cd-timeline">
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-picture bg-primary"><i class="icon-pencil-alt"></i></div>
        <div class="cd-timeline-content">
          <h4>1. Start with this</h4>
          <p class="m-0">
            Make sure you pick out a good luck new job card to go with the words, and pop a beautiful bunch of flowers from our gift range in your basket, to make them feel super special.
          </p>
          <span class="cd-date">Jan <span class="counter"> 14</span></span>
        </div>
      </div>
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-movie bg-secondary"><i class="icon-video-camera"></i></div>
        <div class="cd-timeline-content">
          <h4>2. Video Tutorial</h4>
          <div class="ratio ratio-21x9 m-t-20">
            <iframe src="https://www.youtube.com/embed/wpmHZspl4EM" allowfullscreen></iframe>
          </div>
          <span class="cd-date">Jan <span class="counter">18</span></span>
        </div>
      </div>
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-picture bg-success"><i class="icon-image"></i></div>
        <div class="cd-timeline-content">
          <h4>3. Layout Drafts</h4>
          <img class="img-fluid p-t-20" :src="getImages('banner/1.jpg')" alt="" /><span class="cd-date">Jan <span class="counter">24</span></span>
        </div>
      </div>
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-location bg-info"><i class="icon-pulse"></i></div>
        <div class="cd-timeline-content">
          <h4>4. Audio Tutorial</h4>
          <audio class="m-t-20" controls>
            <source src="@/assets/audio/horse.ogg" type="audio/ogg" />
            Your browser does not support the audio element.</audio
          ><span class="cd-date">Feb <span class="counter">14</span></span>
        </div>
      </div>
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-location bg-warning"><i class="icon-image"></i></div>
        <div class="cd-timeline-content">
          <h4>5. Team Work</h4>
          <img class="img-fluid p-t-20" :src="getImages('banner/3.jpg')" alt="" /><span class="cd-date">Feb <span class="counter">18</span></span>
        </div>
      </div>
      <div class="cd-timeline-block">
        <div class="cd-timeline-img cd-movie bg-danger"><i class="icon-pencil-alt"></i></div>
        <div class="cd-timeline-content">
          <h4>Final Testing</h4>
          <p class="m-0">Explain any new understanding or fresh insights about the problem. This is the content of the Final Testing.</p>
          <span class="cd-date">Feb <span class="counter">26</span></span>
        </div>
      </div>
    </section>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
</script>
