<template>
  <TheBreadcrumbs main="Bonus UI" title="tour" />
  <div class="container-fluid">
    <div class="user-profile">
      <div class="row">
        <ClientOnly>
          <AdvanceTourUserProfile />
          <UserProfileDefaultAccording />
        </ClientOnly>
        <div class="col-xl-9 col-lg-12 col-md-7 xl-65 box-col-65">
          <div class="row">
            <UserProfilePost />
          </div>
        </div>
        <ClientOnly> <VTour ref="tour" :steps="steps" autoStart /></ClientOnly>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
useHead({
  title: 'Bonus UI  Tour | Cion - Premium Nuxt Admin Template',
});
const tour = ref();
interface TourStep {
  target: string;
  content: string;
  params?: {
    placement: string;
  };
}
const tourOptions = ref({
  useKeyboardNavigation: true,
  labels: {
    buttonSkip: 'Skip',
    buttonPrevious: 'Back',
    buttonNext: 'Next',
    buttonStop: 'Done',
  },
});
const toogle = ref<boolean>(true);
const steps = ref<TourStep[]>([
  {
    target: '#profile-tour',
    content: 'This is Profile image',
  },
  {
    target: '#update-profile-tour',
    content: 'Change Profile image here',
  },
  {
    target: '#info-bar-tour',
    content: 'This is the your details',
  },
  {
    target: '#social-bar-tour',
    content: 'This is your Social details',
  },
  {
    target: '#first-post-tour',
    content: 'This is the your first Post',
    params: {
      placement: 'top',
    },
  },
  {
    target: '#last-post-tour',
    content: 'This is the your last Post',
    params: {
      placement: 'top',
    },
  },
]);
onMounted(() => {
  setTimeout(() => {
    if (tour.value) {
      tour.value.resetTour();
    }
  }, 300);
});
</script>
