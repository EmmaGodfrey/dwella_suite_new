<template>
  <div class="col-xl-8 xl-50 col-md-7 box-col-6">
    <div class="tab-content" id="v-pills-tabContent" :style="filter ? 'display: none;' : ''">
      <div
        class="tab-pane contact-tab-0 tab-content-child fade"
        :class="contact.active ? 'active show' : ''"
        :id="'v-pills-user' + contact.id"
        role="tabpanel"
        aria-labelledby="v-pills-user-tab"
        @click="changeDetails(contact)"
        v-for="(contact, index) in contacts"
        :key="index"
      >
        <div class="profile-mail">
          <div class="media align-items-center" for="file">
            <img class="img-100 img-fluid m-r-20 rounded-circle update_img_0" :src="contact.imgUrl || getImages(contact.image)" id="output" alt="" />
            <input
              class="updateimg"
              id="file"
              type="file"
              name="img"
              @change="
                event => {
                  loadFile(event, contact);
                }
              "
            />
            <div class="media-body mt-0">
              <h5>
                <span class="first_name_0">{{ contact.name1 }} </span> <span class="last_name_0">{{ contact.name2 }}</span>
              </h5>
              <p class="email_add_0">{{ contact.email }}</p>
              <ul>
                <li><a href="javascript:void(0)" @click="collapse()">Edit</a></li>
                <li><a href="javascript:void(0)" v-on:click="basicWarningAlert(contact, index)">Delete</a></li>
                <li><a href="javascript:void(0)" @click="collapseFilter()">History</a></li>
                <li><a href="javascript:void(0)" data-bs-toggle="modal" data-bs-target="#printModal" @click="contactView(contact)">Print</a></li>
              </ul>
            </div>
          </div>
          <div class="email-general">
            <h6 class="mb-3">General</h6>
            <ul>
              <li>
                Name <span class="font-primary first_name_0">{{ contact.name1 }}</span>
              </li>
              <li>
                Gender <span class="font-primary">{{ contact.gender }}</span>
              </li>
              <li>
                Birthday<span class="font-primary">
                  <span class="birth_day_0">{{ contact.day }}</span
                  ><span class="birth_month_0 ms-1">{{ contact.month }}</span
                  ><span class="birth_year_0 ms-1">{{ contact.year }}</span></span
                >
              </li>
              <li>
                Personality<span class="font-primary personality_0">{{ contact.personality }}</span>
              </li>
              <li>
                City<span class="font-primary city_0">{{ contact.city }}</span>
              </li>
              <li>
                Mobile No<span class="font-primary mobile_num_0">{{ contact.mobileno }}</span>
              </li>
              <li>
                Email Address <span class="font-primary email_add_0">{{ contact.email }} </span>
              </li>
              <li>
                Website<span class="font-primary url_add_0">{{ contact.website }}</span>
              </li>
              <li>
                Interest<span class="font-primary interest_0">{{ contact.interest }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="contact-editform" :style="filter ? '' : 'display: none;'">
      <form>
        <ContactsEditView />
        <button class="btn btn-secondary update-contact" type="button" @click="collapse()">Save</button>
        <button class="btn btn-primary ms-1" type="button">Cancel</button>
      </form>
    </div>
    <div id="right-history" :class="filtered ? 'show' : ''">
      <div class="modal-header p-3">
        <h6 class="modal-title w-100">
          Contact History<span class="pull-right"
            ><a class="closehistory" href="javascript:void(0)" @click="collapseFilter()"><i class="icofont icofont-close" :class="filtered ? 'show' : ''"></i></a
          ></span>
        </h6>
      </div>
      <ContactsContactHistory />
    </div>
    <ContactsPrintView :contact="detail" />
  </div>
</template>
<script lang="ts" setup>
import swal from 'sweetalert2';

import { getImages } from '~/composables/commen/imgMixin';
import { loadFile, filtered, filter, collapseFilter, collapse } from '~/composables/contectCom';
import { useContactsStore } from '~/store/contacts';

import type personalType from '~/types/personal';

const detail = ref<personalType | null>(null);
const store = useContactsStore();
const { personal } = storeToRefs(store);
const contacts = personal.value;

function contactView(id: personalType) {
  detail.value = id;
}
function basicWarningAlert(value: personalType, index: number) {
  swal
    .fire({
      icon: 'warning',
      title: 'Are you sure?',
      text: 'This contact will be deleted from your Personal Contacts and from the chat list too.',
      showCancelButton: true,
      cancelButtonText: 'Cancel',
      confirmButtonText: 'Ok',
      confirmButtonColor: 'var(--theme-default)',
    })
    .then((result: { isConfirmed: boolean; isDenied: boolean }) => {
      if (result.isConfirmed) {
        contacts.splice(contacts.indexOf(value), 1);
        if (index == contacts.length) {
          if (contacts.length > 0) {
            contacts[0]!.active = true;
          }
        }
        if (contacts.length != index) {
          contacts[index]!.active = true;
        }
      } else {
        swal.fire({
          text: 'Your contact is safe!',
          confirmButtonColor: 'var(--theme-default)',
        });
      }
    });
}
function changeDetails(details: personalType) {
  if (!details.active) {
    contacts.forEach((data: personalType) => {
      if (contacts?.includes(details)) {
        data.active = false;
      }
    });
    details.active = !details.active;
  }
}
</script>
