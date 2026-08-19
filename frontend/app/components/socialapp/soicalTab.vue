<template>
  <div class="col-sm-12 box-col-12">
    <div class="card">
      <div class="social-tab">
        <ul class="nav nav-tabs" id="top-tab" role="tablist">
          <li class="nav-item" v-on:click="changeTab('timeline')">
            <a class="nav-link" :class="{ 'show active': showtab == 'timeline' }" id="top-timeline" data-bs-toggle="tab" role="tab" aria-controls="timeline" aria-selected="false">
              <Icon name="ic:outline-access-time" class="" size="20" />Timline
            </a>
          </li>
          <li class="nav-item" v-on:click="changeTab('about')">
            <a class="nav-link" :class="{ 'show active': showtab == 'about' }" id="top-about" data-toggle="tab" role="tab" aria-controls="about" aria-selected="false">
              <Icon name="tabler:alert-circle" class="" size="20" />About
            </a>
          </li>
          <li class="nav-item" v-on:click="changeTab('friends')">
            <a class="nav-link" :class="{ 'show active': showtab == 'friends' }" id="top-friends" data-toggle="tab" role="tab" aria-controls="friends" aria-selected="false">
              <Icon name="tabler:users" class="" size="20" />Friends
            </a>
          </li>
          <li class="nav-item" v-on:click="changeTab('photos')">
            <a class="nav-link" :class="{ 'show active': showtab == 'photos' }" id="top-photos" data-toggle="tab" role="tab" aria-controls="photos" aria-selected="false">
              <Icon name="material-symbols:imagesmode-outline" class="" size="20" />Photos
            </a>
          </li>
        </ul>
        <div class="input-group">
          <input class="form-control" type="text" placeholder="Search......." /><span class="input-group-text"> <i class="fa fa-search"></i></span>
        </div>
      </div>
    </div>
  </div>
  <div class="tab-content" id="top-tabContent">
    <div class="tab-pane fade" :class="{ 'show active': showtab == 'timeline' }" id="timeline" role="tabpanel" aria-labelledby="timeline">
      <SocialappTimelineIndexTimeline />
    </div>
    <div class="tab-pane fade" :class="{ 'show active': showtab == 'about' }" id="about" role="tabpanel" aria-labelledby="about">
      <SocialappAboutIndexAbout />
    </div>
    <div class="tab-pane fade" :class="{ 'show active': showtab == 'friends' }" id="friends" role="tabpanel" aria-labelledby="friends">
      <SocialappSocialFrinds />
    </div>
    <div class="tab-pane fade" :class="{ 'show active': showtab == 'photos' }" id="photos" role="tabpanel" aria-labelledby="photos">
      <SocialappPhotosView />
    </div>
  </div>
</template>
<script lang="ts" setup>
const showtab = ref<string>('timeline');
function changeTab(tab: string) {
  showtab.value = tab;
}
</script>
