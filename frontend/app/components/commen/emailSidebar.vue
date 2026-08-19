<template>
  <div class="col-xl-3 col-md-6">
    <div class="email-sidebar">
      <a class="btn btn-primary email-aside-toggle" href="javascript:void(0)" @click="collapseFilter()">email filter</a>
      <div class="email-left-aside" :class="filtered ? 'open' : ''">
        <div class="card">
          <div class="card-body">
            <div class="email-app-sidebar">
              <div class="media">
                <div class="media-size-email"><img class="me-3 rounded-circle img-50 me-2" :src="getImages('user/user.png')" alt="" /></div>
                <div class="media-body">
                  <h6 class="f-w-600">MARKJENCO</h6>
                  <p>Markjecno@gmail.com</p>
                </div>
              </div>
              <ul class="nav main-menu" role="tablist">
                <li class="nav-item">
                  <nuxt-link class="btn-primary btn-block btn-mail w-100" id="pills-darkhome-tab" to="/email/email_compose"><i class="icofont icofont-envelope me-2"></i> NEW MAIL</nuxt-link>
                </li>
                <li class="nav-item">
                  <nuxt-link class="show" id="pills-darkprofile-tab" to="/email/email_inbox?layout=default">
                    <span class="title"><i class="icon-import"></i> Inbox</span><span class="badge pull-right">(236)</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-folder"></i> All mail</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-new-window"></i> Sent</span><span class="badge pull-right">(69)</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-pencil-alt"></i> DRAFT</span><span class="badge pull-right">(59)</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-trash"></i> TRASH</span><span class="badge pull-right">(99)</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-info-alt"></i> IMPORTANT</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-star"></i> Starred</span></nuxt-link
                  >
                </li>
                <li>
                  <hr />
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-email"></i> UNREAD</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-export"></i> SPAM</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-share"></i> OUTBOX</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-file"></i> UPDATE</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-bell"></i> ALERT</span></nuxt-link
                  >
                </li>
                <li>
                  <nuxt-link to="/email/email_inbox?layout=default"
                    ><span class="title"><i class="icon-notepad"></i> NOTES</span><span class="badge pull-right">(20)</span></nuxt-link
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
