<template>
  <div>
    <div class="page-wrapper">
      <div class="container-fluid p-0 m-0">
        <div class="comingsoon comingsoon-bgimg">
          <div class="comingsoon-inner text-center">
            <img src="/images/logo/logo-1.png" alt="" />
            <h5>WE ARE COMING SOON</h5>
            <div class="countdown">
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
  title: 'Comingsoon Image | Cion - Premium Vue Admin Template',
});
</script>
