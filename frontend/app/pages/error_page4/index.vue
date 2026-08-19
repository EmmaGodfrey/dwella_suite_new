<template>
  <div>
    <div class="page-wrapper compact-wrapper" id="pageWrapper">
      <div class="error-wrapper">
        <div class="container">
          <div class="error-page1">
            <div class="svg-wrraper">
              <ErrorSvgErrorPage4 />
            </div>
            <div class="col-md-8 offset-md-2">
              <h3>500 - Internal server error</h3>
              <p class="sub-content">The page you are attempting to reach is currently not available. This may be because the page does not exist or has been moved.</p>
              <nuxt-link class="btn btn-primary btn-lg" :to="{ path: '/' }">BACK TO HOME PAGE</nuxt-link>
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
  title: 'Error Page4 | Cion - Premium Vue Admin Template',
});
</script>
