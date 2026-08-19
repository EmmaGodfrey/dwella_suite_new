<template>
  <div class="col-xl-3 box-col-3 xl-30">
    <div class="email-sidebar">
      <a class="btn btn-primary email-aside-toggle" href="javascript:void(0)" @click="collapseFilter()">bookmark filter</a>
      <div class="email-left-aside" :class="filtered ? 'open' : ''">
        <div class="card">
          <div class="card-body">
            <div class="email-app-sidebar left-bookmark">
              <div class="media">
                <div class="media-size-email"><img class="me-3 rounded-circle" src="/images/user/user.png" alt="" /></div>
                <div class="media-body">
                  <nuxt-link to="/users/profile">
                    <h6 class="f-w-600">MARK JENCO</h6>
                  </nuxt-link>
                  <p>Markjecno@gmail.com</p>
                </div>
              </div>
              <ul class="nav main-menu" role="tablist">
                <li class="nav-item">
                  <button class="badge-light btn-block btn-mail" type="button" data-bs-toggle="modal" data-bs-target="#bookmarkmodal" @click="show = true">
                    <Icon name="material-symbols:bookmarks-outline" class="me-2" size="20" />New Bookmark
                  </button>
                </li>
                <li class="nav-item"><span class="main-title"> Views</span></li>
                <li>
                  <a id="pills-created-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-created" aria-selected="true"
                    ><span class="title" v-on:click="says('pills_created')"> Created by me</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-favourites-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-favourites" aria-selected="false"
                    ><span class="title" v-on:click="says('pills_favourites')"> Favourites ({{ favourite.length }})</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-shared-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-shared" aria-selected="false"
                    ><span class="title" v-on:click="says('pills_shared')"> Shared with me</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-bookmark-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-bookmark" aria-selected="false"
                    ><span class="title" v-on:click="says('pills_bookmark')"> My bookmark</span></a
                  >
                </li>
                <li>
                  <hr />
                </li>
                <li>
                  <span class="main-title">
                    Tags<span class="pull-right"
                      ><a href="javascript:void(0)" data-bs-toggle="modal" data-bs-target="#createtag"> <Icon name="iconamoon:sign-plus-circle-light" class=" " size="20" /> </a></span
                  ></span>
                </li>
                <li>
                  <a class="show" id="pills-notification-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-notification" aria-selected="false"
                    ><span class="title" @click="says('pills_notification')"> notification</span></a
                  >
                </li>
                <li>
                  <a class="show" id="pills-newsletter-tab" data-toggle="pill" href="javascript:void(0)" role="tab" aria-controls="pills-newsletter" aria-selected="false"
                    ><span class="title" @click="says('pills_newsletter')"> Newsletter</span></a
                  >
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-xl-9 col-md-12 box-col-9 xl-70">
    <div class="email-right-aside bookmark-tabcontent">
      <div class="card email-body radius-left">
        <div class="ps-0">
          <div class="tab-content">
            <BookmarkCreatedBy />
            <BookmarkFavouritesView />
            <BookmarkSharedTab />
            <BookmarkMyBookmark />
            <BookmarkNotificationView />
            <BookmarkNewsLetter />
            <BookmarkNewBookmark />

            <BookmarkTagsView />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useProjectStore } from '~/store/project';

const show = ref<boolean>(false);
const filtered = ref<boolean>(false);
const store = useProjectStore();
const { favourite } = storeToRefs(store);
const { say } = store;
function collapseFilter() {
  filtered.value = !filtered.value;
}
function says(message: string) {
  say(message);
}
</script>
