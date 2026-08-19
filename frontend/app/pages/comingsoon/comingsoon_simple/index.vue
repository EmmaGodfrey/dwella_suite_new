<template>
  <div>
    <div class="page-wrapper">
      <div class="container-fluid p-0">
        <div class="comingsoon">
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
  title: 'Comingsoon Page | Cion - Premium Vue Admin Template',
});
</script>
