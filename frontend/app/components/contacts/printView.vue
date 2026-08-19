<template>
  <div class="modal fade modal-bookmark" id="printModal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document" :id="contact?.id">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Print preview</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body list-persons">
          <div class="profile-mail pt-0" id="DivIdToPrint">
            <div class="d-flex">
              <img v-if="contact?.image" class="img-100 img-fluid m-r-20 rounded-circle" id="updateimg" :src="contact.imgUrl || getImages(contact.image)" alt="" />
              <div class="flex-grow-1 mt-0">
                <h5>
                  <span id="printname">{{ contact?.name1 }}</span> <span id="printlast">{{ contact?.name2 }}</span>
                </h5>
                <p id="printmail">{{ contact?.email }}</p>
              </div>
            </div>
            <div class="email-general">
              <h6>General</h6>
              <p>
                Email Address: <span class="font-primary" id="mailadd">{{ contact?.email }} </span>
              </p>
            </div>
          </div>
          <button class="btn btn-secondary" id="btnPrint" type="button">Print</button>
          <button class="btn btn-primary ms-1" type="button" data-bs-dismiss="modal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';

import type personalType from '~/types/personal';

let props = defineProps<{
  contact: personalType | null;
}>();
</script>
