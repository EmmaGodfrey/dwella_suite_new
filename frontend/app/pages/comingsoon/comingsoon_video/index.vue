<template>
  <div>
    <div class="page-wrapper">
      <div class="container-fluid p-0">
        <div class="comingsoon auth-bg-video">
          <video class="bgvideo-comingsoon" id="bgvid" muted autoplay poster="/images/logo/logo-1.png">
            <source src="/video/auth-bg.mp4" type="video/mp4" />
          </video>
          <div class="comingsoon-inner text-center">
            <img src="/images/logo/logo-1.png" alt="" />
            <h5>WE ARE COMING SOON</h5>
            <div class="countdown" id="clockdiv">
              <CommenComingsoonTimer />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
definePageMeta({
  layout: 'custom',
});
useHead({
  title: 'Comingsoon Video | Cion - Premium Vue Admin Template',
});
</script>
