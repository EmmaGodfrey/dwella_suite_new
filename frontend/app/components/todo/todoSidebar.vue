<template>
  <div class="col-xl-3">
    <div class="email-sidebar md-sidebar">
      <a class="btn btn-primary email-aside-toggle md-sidebar-toggle" @click="collapseFilter()">To Do filter</a>
      <div class="email-left-aside md-sidebar-aside" :class="filtered ? 'open' : ''">
        <div class="card">
          <div class="card-body">
            <div class="email-app-sidebar left-bookmark custom-scrollbar">
              <div class="d-flex align-items-center">
                <div class="media-size-email"><img class="me-3 img-40 rounded-circle" :src="getImages('user/user.png')" alt="" /></div>
                <div class="flex-grow-1">
                  <h6 class="f-w-600">Mark Jecno</h6>
                  <p>Markjecno@gmail.com</p>
                </div>
              </div>
              <ul class="nav main-menu">
                <li class="nav-item">
                  <button class="btn-primary badge-light btn-block btn-mail w-100" type="button" data-bs-toggle="modal" data-bs-target="#exampleModal">
                    <Icon name="lucide:check-circle" class="me-2" size="20" /> To Do List
                  </button>
                </li>

                <li class="nav-item">
                  <a href="javascript:void(0)"
                    ><span class="iconbg badge-light-primary"> <Icon name="tabler:file-plus" class="" size="20" /> </span><span class="title ms-2">All Task</span></a
                  >
                </li>
                <li class="nav-item">
                  <a href="javascript:void(0)"
                    ><span class="iconbg badge-light-success"> <Icon name="lucide:check-circle" class="" size="20" /> </span><span class="title ms-2">Completed</span
                    ><span class="badge badge-success">3</span></a
                  >
                </li>
                <li class="nav-item">
                  <a href="javascript:void(0)"
                    ><span class="iconbg badge-light-danger"> <Icon name="ic:twotone-cast" class="" size="20" /> </span><span class="title ms-2">Pending</span
                    ><span class="badge badge-danger">2</span></a
                  >
                </li>
                <li class="nav-item">
                  <a href="javascript:void(0)"
                    ><span class="iconbg badge-light-info"> <Icon name="humbleicons:activity" class="" size="20" /> </span><span class="title ms-2">In Process</span
                    ><span class="badge badge-primary">2</span></a
                  >
                </li>
                <li class="nav-item">
                  <a href="javascript:void(0)"
                    ><span class="iconbg badge-light-danger"> <Icon name="iconamoon:trash-simple" class="" size="20" /> </span><span class="title ms-2">Trash</span></a
                  >
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';

const filtered = ref<boolean>(false);
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
