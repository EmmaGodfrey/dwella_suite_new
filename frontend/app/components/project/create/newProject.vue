<template>
  <div class="form theme-form">
    <div class="row">
      <div class="col">
        <div class="mb-3">
          <label>Project Title</label>
          <input class="form-control" type="text" :class="titleInputClasses" placeholder="Project name *" v-model="title" @input="validated(($event.target as HTMLInputElement).value)" />
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="mb-3">
          <label>Client name</label>
          <input class="form-control" type="text" placeholder="Name client or company name" />
        </div>
      </div>
    </div>
    <ProjectCreateProjectRate />
    <div class="row">
      <div class="col">
        <div class="mb-3">
          <label>Enter some Details</label>
          <textarea class="form-control" id="exampleFormControlTextarea4" rows="3" v-model="desc" :class="descInputClasses" @input="update(($event.target as HTMLTextAreaElement).value)"></textarea>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="mb-3">
          <label>Upload project file</label>
          <CommenDropZones />
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="text-end"><a class="btn btn-success me-3" target="_blank" @click="add()"> Add</a><a class="btn btn-danger" href="javascript:void(0)">Cancel</a></div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useRouter } from 'vue-router';

import { useProjectStore } from '~/store/project';

const store = useProjectStore();
const { data } = storeToRefs(store);
const allprojects = data.value;
const titleInputClasses = ref<string>('is-invalid');
const descInputClasses = ref<string>('is-invalid');
const formSubmitted = ref<boolean>(false);
const titleError = ref<boolean>(false);
const descError = ref<boolean>(false);
const errors = ref<string | number[]>([]);
const title = ref<string>('');
const desc = ref<string>('');
const router = useRouter();
function add() {
  formSubmitted.value = true;
  errors.value = [];
  if (title.value.length < 5 || desc.value.length < 5) {
    titleError.value = true;
    descError.value = true;
    errors.value.push();
  } else {
    titleError.value = false;
    descError.value = false;
    errors.value.push();
    const arr = {
      id: 1,
      title: title.value,
      badge: 'Doing',
      type: 'primary progress-bar-striped',
      font: 'primary',
      img: 'user/3.jpg',
      sites: 'Themeforest, australia',
      desc: desc.value,
      issue: '12',
      resolved: '5',
      comment: '7',
      like: '+10',
      progress: '70',
      customers_img1: 'user/3.jpg',
      customers_img2: 'user/5.png',
      customers_img3: 'user/1.jpg',
    };
    allprojects.push(arr);
    router.replace('/project/project_list');
  }
}

function validated(value: string) {
  if (value.length < 5) {
    titleInputClasses.value = 'is-invalid';
  } else {
    titleInputClasses.value = 'is-valid';
  }
}
function update(value: string) {
  if (value.length < 4) {
    descInputClasses.value = 'is-invalid';
  } else {
    descInputClasses.value = 'is-valid';
  }
}
</script>
