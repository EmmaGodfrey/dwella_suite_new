<template>
  <div class="tab-pane fade" v-bind:class="activeclass === 'pills_created' ? 'active show' : ''" id="pills-created" role="tabpanel" aria-labelledby="pills-created-tab">
    <div class="card mb-0">
      <div class="card-header d-flex">
        <h6 class="mb-0">Created by me</h6>
        <ul>
          <li>
            <a class="grid-bookmark-view" href="javascript:void(0);">
              <Icon name="akar-icons:grid" class=" " size="20" @click="liststyle = !liststyle" />
            </a>
          </li>
          <li>
            <a class="list-layout-view" href="javascript:void(0);">
              <Icon name="ic:outline-format-list-bulleted" class=" " size="20" @click="liststyle = !liststyle" />
            </a>
          </li>
        </ul>
      </div>
      <div class="card-body pb-0">
        <div class="details-bookmark text-center" v-bind:class="{ 'list-bookmark': liststyle }">
          <div class="row" id="bookmarkData">
            <div class="col-xl-3 col-sm-6 xl-50 box-col-6" v-for="(item, index) in bookmark" :key="index">
              <div class="card card-with-border bookmark-card o-hidden">
                <div class="details-website">
                  <img class="img-fluid" :src="getImages(item.image)" alt="" />
                  <div class="favourite-icon favourite_0" :class="getActive(item.id) ? 'favourite' : ''" @click="setFavourite(item)">
                    <a href="javascript:void(0)"><i class="fa fa-star"></i></a>
                  </div>
                  <div class="desciption-data">
                    <div class="title-bookmark">
                      <h6 class="title_0">{{ item.title }}</h6>
                      <p class="weburl_0">{{ item.website_url }}</p>
                      <div class="hover-block">
                        <ul>
                          <li>
                            <a data-bs-toggle="modal" data-bs-target="#edit-bookmark">
                              <Icon name="lucide:edit-2" class=" " size="20" />
                            </a>
                          </li>
                          <li>
                            <a href="/app/bookmark">
                              <Icon name="solar:link-outline" class=" " size="20" />
                            </a>
                          </li>
                          <li>
                            <a href="/app/bookmark">
                              <Icon name="lucide:share-2" class=" " size="20" />
                            </a>
                          </li>
                          <li>
                            <a>
                              <Icon name="octicon:trash-24" class=" " size="20" @click="basicWarningAlert(index)" />
                            </a>
                          </li>
                          <li class="pull-right text-end">
                            <a href="/app/bookmark">
                              <Icon name="ph:tag" class=" " size="20" />
                            </a>
                          </li>
                        </ul>
                      </div>
                      <div class="content-general">
                        <p class="desc_0">{{ item.desc }}</p>
                        <span class="collection_0">General</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <BookmarkEditView />
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

import { getImages } from '~/composables/commen/imgMixin';
import { useProjectStore } from '~/store/project';
import type { DataItem } from '~/types/common';

const liststyle = ref<boolean>(false);
const store = useProjectStore();
const { activeclass, favourite, bookmark } = storeToRefs(store);

function basicWarningAlert(index: number) {
  swal
    .fire({
      icon: 'warning',
      title: 'Are you sure?',
      text: 'This bookmark will be deleted from your bookmark ',
      showCancelButton: true,
      cancelButtonText: 'Cancel',
      confirmButtonText: 'Ok',
      confirmButtonColor: 'var(--theme-default)',
    })
    .then(result => {
      if (result) {
        bookmark.value.splice(index, 1);
        swal.fire({
          icon: 'success',
          text: 'Poof! Your imaginary file has been deleted!',
          confirmButtonColor: 'var(--theme-default)',
        });
      } else {
        swal.fire({ text: 'Your contact is safe!', confirmButtonColor: 'var(--theme-default)' });
      }
    });
}
function getActive(itemId: number) {
  const objIndex = favourite.value.findIndex(obj => obj.id === itemId);
  if (objIndex > -1) {
    return true;
  } else {
    return false;
  }
}
function setFavourite(item: DataItem) {
  const objIndex = favourite.value.findIndex(obj => obj.id === item.id);
  if (objIndex > -1) {
    favourite.value.splice(objIndex, 1);
  } else {
    favourite.value.push(item);
  }
}
</script>
