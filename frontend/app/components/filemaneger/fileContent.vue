<template>
  <div class="col-xl-9 col-md-12 box-col-9 xl-70">
    <div class="file-content">
      <div class="card">
        <div class="card-header">
          <div class="media">
            <form class="form-inline" action="#" method="get">
              <div class="form-group d-flex mb-0">
                <i class="fa fa-search"></i>
                <input class="form-control-plaintext" type="text" placeholder="Search..." />
              </div>
            </form>
            <div class="media-body text-end">
              <form class="d-inline-flex" action="#" method="POST" enctype="multipart/form-data" name="myForm">
                <div class="btn btn-primary"><Icon name="ci:add-plus-square" class="" size="20" />Add New</div>
                <div style="height: 0px; width: 0px; overflow: hidden">
                  <input id="upfile" type="file" />
                </div>
              </form>
              <div class="btn btn-outline-primary ms-2" type="file"><Icon name="octicon:upload-16" class="" size="20" />Upload</div>
            </div>
          </div>
        </div>
        <div class="card-body file-manager">
          <h5>Quick Access</h5>
          <ul class="quick-file d-flex">
            <li v-for="(item, index) in quick" :key="index">
              <div class="quick-box"><i class="fa" :class="item.icon"></i></div>
              <h6>{{ item.title }}</h6>
            </li>
          </ul>
          <h5 class="mt-4">Folders</h5>
          <ul class="folder">
            <li class="folder-box" v-for="(item, index) in folder" :key="index">
              <div class="d-block">
                <i class="f-44 txt-warning fa" :class="item.icon"></i>
                <div class="mt-3">
                  <i class="fa fa-ellipsis-v ellips"></i>
                  <h6 class="mb-1">{{ item.name }}</h6>
                  <p>
                    {{ item.file }}<span class="pull-right"> <i class="fa fa-clock-o"> </i> {{ item.hour }}</span>
                  </p>
                </div>
              </div>
            </li>
          </ul>
          <h5 class="mt-4">Files</h5>
          <ul class="d-flex flex-row files-content">
            <li class="folder-box d-flex align-items-center" v-for="(item, index) in file" :key="index">
              <div class="d-flex align-items-center files-list">
                <div class="flex-shrink-0 file-left"><i class="f-22 fa" :class="item.icon"></i></div>
                <div class="flex-grow-1 ms-3">
                  <h6>{{ item.name }}</h6>
                  <p>{{ item.day }}</p>
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
import { useFilemanegerStore } from '~/store/filemaneger';

const store = useFilemanegerStore();
const { folders, files, quick } = storeToRefs(store);
const folder = folders.value;
const file = files.value;
</script>
