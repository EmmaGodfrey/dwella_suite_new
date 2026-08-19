<template>
  <div class="card-body">
    <form class="theme-form sm-form">
      <div class="mb-3">
        <div class="row">
          <label class="col-xl-2 col-sm-12 col-md-12 col-form-label">Placement</label>
          <div class="col-xl-4 col-sm-12 col-md-6 mb-4">
            <select v-model="enterNotify" class="form-select form-control" id="bootstrap-notify-placement-from">
              <option v-for="(anim, index) in notifyList" :value="anim.position" :key="index">{{ anim.position }}</option>
            </select>
          </div>
        </div>
        <div class="row">
          <label class="col-xl-2 col-sm-12 col-md-12 col-form-label">Icon</label>
          <div class="col-xl-4 col-md-12 col-sm-12 mb-4">
            <select v-model="enterIcon" class="form-select form-control" id="bootstrap-notify-placement-from">
              <option v-for="(anim, index) in notifyList" :value="anim.icon" :key="index">{{ anim.icon }}</option>
            </select>
          </div>
        </div>
      </div>
    </form>
  </div>
  <div class="card-footer">
    <div class="col-sm-12">
      <client-only>
        <notifications :position="enterNotify" type="success">
          <template #body="props">
            <div class="vue-notification">
              <i :class="enterIcon"></i>
              <p class="title">
                {{ props.item.title }}
              </p>
            </div>
          </template>
        </notifications></client-only
      >
      <button class="btn btn-primary" id="bootstrap-notify-gen-btn" @click.prevent="showNotify">Display notify</button>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useNotification } from '@kyvg/vue3-notification';

interface notifys {
  position: string;
  icon: string;
}
const enterNotify = ref<string>('top left');
const enterIcon = ref<string>('none');
const { notify } = useNotification();
const notifyList = ref<notifys[]>([
  { icon: 'none', position: '' },
  { position: 'top left', icon: 'fa fa-check-square' },
  { position: 'top right', icon: 'fa fa-warning' },
  { position: 'bottom left', icon: 'fa fa-cloud-download' },
  { position: 'bottom right', icon: 'fa fa-unlock-alt' },
]);
function showNotify() {
  notify({
    title: 'New Order has been placed',
    closeOnClick: true,
  });
}
</script>
