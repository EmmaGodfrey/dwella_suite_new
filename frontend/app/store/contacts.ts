import { computed } from 'vue';

import { defineStore } from 'pinia';

import contacts from '~/data/contacts.json';
import Organization from '~/types/organization';
import personalType from '~/types/personal';

export const useContactsStore = defineStore('contacts', () => {
  const personal = ref<personalType[]>(contacts.personal);
  const organization = ref<Organization[]>(contacts.organization);
  const selectedContact = ref<personalType[]>(contacts.personal);
  const currentcontact = ref<object>({});

  const setSelectedContact = computed(value => {});

  return {
    personal,

    organization,
    selectedContact,
    setSelectedContact,

    currentcontact,
  };
});
