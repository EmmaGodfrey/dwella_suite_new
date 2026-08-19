<template>
  <div class="modal fade modal-bookmark" id="contectmodel" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="exampleModalLabel">Add Contact</h5>
          <button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <form class="form-bookmark needs-validation" id="bookmark-form" novalidate>
            <div class="row g-2">
              <div class="mb-3 col-md-12 mt-0">
                <label for="con-name">Name</label>
                <div class="row">
                  <div class="col-sm-6">
                    <input class="form-control" id="con-name" type="text" v-model="name1" placeholder="First Name" autocomplete="off" />
                  </div>
                  <div class="col-sm-6">
                    <input class="form-control" id="con-last" type="text" v-model="name2" placeholder="Last Name" autocomplete="off" />
                  </div>
                </div>
              </div>
              <div class="mb-3 col-md-12 mt-0">
                <label for="con-mail">Email Address</label>
                <input class="form-control" id="con-mail" type="email" v-model="email" autocomplete="off" />
              </div>
              <div class="mb-3 col-md-12 my-0">
                <label for="con-phone">Phone</label>
                <div class="row">
                  <div class="col-sm-6">
                    <input class="form-control" id="con-phone" v-model="mobile" type="tel" autocomplete="off" />
                  </div>
                  <div class="col-sm-6">
                    <select class="form-control" id="con-select">
                      <option>Mobile</option>
                      <option>Work</option>
                      <option>Others</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            <input id="index_var" type="hidden" value="5" />
            <button class="btn btn-secondary" type="button" target="_blank" @click="submitContact()" data-bs-dismiss="modal">Save</button>
            <button class="btn btn-primary ms-1" type="button" data-bs-dismiss="modal">Cancel</button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useContactsStore } from '~/store/contacts';
import personalType from '~/types/personal';

const name1 = ref<string>('');
const name2 = ref<string>('');
const email = ref<string>(' ');
const mobile = ref<string>('');
const id = ref<string>('');
const formSubmitted = ref<boolean>(false);
const name1Error = ref<boolean>(false);
const name2Error = ref<boolean>(false);
const errors = ref<string | number[]>([]);
const store = useContactsStore();
const { personal } = storeToRefs(store);
const contacts: personalType[] = personal.value;
function submitContact() {
  formSubmitted.value = true;
  errors.value = [];
  if (name2.value.length < 5 || name1.value.length < 5) {
    name2Error.value = true;
    name1Error.value = true;
    errors.value.push();
  } else {
    name2Error.value = false;
    name1Error.value = false;
    errors.value.push();
    const arr: personalType = {
      image: 'user/5.png',
      name2: name2.value,
      name1: name1.value,
      email: email.value,
      mobileno: mobile.value,
      gender: 'Male',
      day: '18',
      month: ' May',
      year: '1994',
      personality: 'Cool',
      city: 'moline acres',
      website: 'www.test.com',
      interest: 'photography',
    };
    contacts.push(arr);
  }
}
</script>
