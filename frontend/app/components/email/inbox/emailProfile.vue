<template>
  <div class="xl-70 box-col-8 col-md-12 col-xl-9">
    <div class="email-right-aside">
      <div class="email-body card">
        <div class="email-profile">
          <div>
            <div class="pe-0 b-r-light"></div>
            <div class="email-top">
              <div class="row">
                <div class="col-12">
                  <div class="media">
                    <label for="chk-ani" class="email-chek d-block form-label"><input id="chk-ani" type="checkbox" class="checkbox_animated" /></label>
                    <div class="media-body">
                      <div class="dropdown">
                        <div class="dropdown">
                          <button type="button" aria-haspopup="true" aria-expanded="false" class="dropdown-toggle btn btn-primary">Action</button>
                          <div tabindex="-1" role="menu" aria-hidden="true" class="dropdown-menu">
                            <button type="button" tabindex="0" role="menuitem" class="dropdown-item dropdown-item">Refresh</button
                            ><button type="button" tabindex="0" role="menuitem" class="dropdown-item dropdown-item">Mark as important</button
                            ><button type="button" tabindex="0" role="menuitem" class="dropdown-item dropdown-item">Move to spam</button
                            ><button type="button" tabindex="0" role="menuitem" class="dropdown-item dropdown-item">Move to Trash</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="inbox">
              <div class="media" v-for="(item, index) in email" :key="index">
                <div class="media-size-email">
                  <label for="chk-ani" class="d-block mb-0 form-label"><input id="chk-ani" type="checkbox" class="checkbox_animated" /></label>
                  <img :src="getImages(item.image ?? '')" alt="" class="me-3 rounded-circle" />
                </div>
                <a href="/viho/app/email/readmail">
                  <div class="media-body">
                    <h6>{{ item.name }}</h6>
                    <p>{{ item.desc }}</p>
                    <span>{{ item.time }}</span>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { getImages } from '~/composables/commen/imgMixin';
import { useEmaillStore } from '~/store/emaill';

const store = useEmaillStore();
const { data } = storeToRefs(store);
const email = data.value;
</script>
