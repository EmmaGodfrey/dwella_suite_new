<template>
  <div class="col-xl-3 xl-30">
    <div class="email-sidebar">
      <a class="btn btn-primary email-aside-toggle" href="javascript:void(0)" @click="collapseFilter()">contact filter </a>
      <div class="email-left-aside" :class="filtered ? 'open' : ''">
        <div class="card">
          <div class="card-body">
            <div class="email-app-sidebar left-bookmark">
              <div class="media">
                <div class="media-size-email"><img class="me-3 rounded-circle" src="/images/user/user.png" alt="" /></div>
                <div class="flex-grow-1 ms-2">
                  <nuxt-link to="/users/profile">
                    <h6 class="f-w-700">MARK JENCO</h6>
                  </nuxt-link>
                  <p>Markjecno@gmail.com</p>
                </div>
              </div>
              <ul class="nav main-menu contact-options" role="tablist">
                <li class="nav-item">
                  <button class="badge-light badge-light btn-block btn-mail w-100" type="button" data-bs-toggle="modal" data-bs-target="#contectmodel">
                    <Icon name="uil:users-alt" class="me-2" size="20" /> New Contacts
                  </button>
                </li>
                <li class="nav-item"><span class="main-title"> Views</span></li>
                <li>
                  <a id="pills-personal-tab" data-bs-toggle="pill" href="#pills-personal" role="tab" aria-controls="pills-personal" aria-selected="true"
                    ><span class="title" v-on:click="say('pills_personal')"> Personal</span></a
                  >
                </li>
                <li>
                  <button class="btn btn-category" type="button" data-bs-toggle="modal" data-bs-target="#exampleModal1"><span class="title"> + Add Category</span></button>
                </li>
                <li>
                  <a class="show" id="pills-organization-tab" data-bs-toggle="pill" href="#pills-organization" role="tab" aria-controls="pills-organization" aria-selected="false"
                    ><span class="title" v-on:click="say('pills_organization')"> Organization</span></a
                  >
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Follow up</span></a>
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Favorites</span></a>
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Ideas</span></a>
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Important</span></a>
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Business</span></a>
                </li>
                <li>
                  <a href="javascript:void(0)"><span class="title">Holidays</span></a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-xl-9 col-md-12 box-col-8 xl-70">
    <div class="email-right-aside bookmark-tabcontent contacts-tabs">
      <div class="card email-body radius-left">
        <div class="ps-0">
          <div class="tab-content">
            <div class="tab-pane fade" id="pills-personal" v-bind:class="activeClass === 'pills_personal' ? 'active show' : ''" role="tabpanel" aria-labelledby="pills-personal-tab">
              <ContactsPersonalView />
            </div>
            <div class="fade tab-pane" v-bind:class="activeClass === 'pills_organization' ? 'active show' : ''" id="pills-organization" role="tabpanel" aria-labelledby="pills-organization">
              <ContactsOrganizationView />
            </div>
            <ContactsAddCategory />
            <ContactsNewContact />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const activeClass = ref<string>('pills_personal');
const filtered = ref<boolean>(false);

function say(message: string) {
  activeClass.value = message;
}
function collapseFilter() {
  filtered.value = !filtered.value;
}
</script>
