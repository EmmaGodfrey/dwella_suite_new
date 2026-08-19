<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Basic Modal</h5>
      </div>
      <div class="card-body btn-showcase">
        <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-original-title="test" data-bs-target="#exampleModal">Simple</button>
        <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLabel">Modal title</h5>
                <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">...</div>
              <div class="modal-footer">
                <button class="btn btn-primary" type="button" data-bs-dismiss="modal">Close</button>
                <button class="btn btn-secondary" type="button">Save changes</button>
              </div>
            </div>
          </div>
        </div>

        <button class="btn btn-primary" type="button" data-bs-toggle="modal" data-bs-target="#exampleModalLong">Scrolling long content</button>
        <div class="modal fade" id="exampleModalLong" tabindex="-1" role="dialog" aria-labelledby="exampleModalLongTitle" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="exampleModalLongTitle">Modal title</h5>
                <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <p v-for="(item, index) in data" :key="index">{{ item.desc }}</p>
              </div>
              <div class="modal-footer">
                <button class="btn btn-secondary" type="button" data-bs-dismiss="modal">Close</button>
                <button class="btn btn-primary" type="button">Save changes</button>
              </div>
            </div>
          </div>
        </div>
        <UikitsModalVerticallyModal />
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useUikitStore } from '~/store/uikit';

const store = useUikitStore();
const { data } = storeToRefs(store);
</script>
