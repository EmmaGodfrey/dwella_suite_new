<template>
  <div class="col-md-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="card-title">Select-2</h5>
      </div>
      <div class="card-body o-hidden">
        <div class="mb-2">
          <div class="col-form-label">Default Placeholder</div>
          <multiselect
            v-model="multiValue"
            tag-placeholder="Add this as new tag"
            placeholder="Select Your Name"
            label="name"
            track-by="code"
            :options="options"
            :multiple="true"
            :taggable="true"
          ></multiselect>
        </div>
        <div class="mb-2">
          <div class="col-form-label">Select2 single select</div>
          <multiselect
            v-model="Value"
            :options="options1"
            :searchable="false"
            group-values="libs"
            group-label="language"
            :group-select="true"
            :close-on-select="false"
            track-by="name"
            label="name"
            placeholder="Pick a value"
          >
          </multiselect>
        </div>
        <div class="mb-2">
          <label class="col-form-label">Select2 multi select</label>
          <multiselect
            v-model="multiValue3"
            tag-placeholder="Add this as new tag"
            placeholder="Select Your Name"
            label="name"
            track-by="code"
            :options="options"
            :multiple="true"
            :taggable="true"
          ></multiselect>
        </div>
        <div class="mb-2">
          <label class="col-form-label">RTL support</label>
          <multiselect
            v-model="multiValue2"
            tag-placeholder="Add this as new tag"
            placeholder="Select Your Name"
            label="name"
            track-by="code"
            :options="options"
            :multiple="true"
            dir="rtl"
            :taggable="true"
          >
          </multiselect>
        </div>
        <div class="mb-2">
          <label class="col-form-label">Limiting The Number Of Selections</label>
          <multiselect
            v-model="multiValue1"
            tag-placeholder="Add this as new tag"
            placeholder="Select Your Name"
            label="name"
            track-by="code"
            :options="options"
            :multiple="true"
            :taggable="true"
          ></multiselect>
        </div>
        <div class="mb-2">
          <label class="col-form-label">Disabled Results</label>
          <multiselect v-model="value" :options="options4" :searchable="false" :group-select="true" :close-on-select="false" track-by="name" label="name" placeholder="Pick a value"></multiselect>
        </div>
        <FormsFormwidgetsSelect2SearchBox />
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import multiselect from 'vue-multiselect';

interface multi {
  code: number;
  name: string;
}
interface open {
  language: string;
  libs: lib[];
}
interface lib {
  name: string;
  category: string;
}
const multiValue = ref<string[]>([]);
const multiValue1 = ref<string[]>([]);
const multiValue2 = ref<string[]>([]);
const multiValue3 = ref<string[]>([]);
const Value = ref<string[]>([]);
const value = ref<string[]>([]);
const options = ref<multi[]>([
  { code: 1, name: 'Alabama' },
  { code: 2, name: 'Wyoming' },
  { code: 3, name: 'Coming' },
  { code: 4, name: 'Hanry Die' },
  { code: 5, name: 'John Doe' },
]);
const options1 = ref<open[]>([
  {
    language: 'Developer',
    libs: [
      { name: 'Alabama', category: 'Front-end' },
      { name: 'Wyoming', category: 'Backend' },
    ],
  },
  {
    language: 'Designer',
    libs: [
      { name: 'Peter', category: 'Backend' },
      { name: 'Hanry Die', category: 'Backend' },
      { name: 'John Doe', category: 'Backend' },
    ],
  },
]);

const options4 = ref<multi[]>([
  { code: 1, name: 'First' },
  { code: 2, name: 'second(disable)' },
  { code: 3, name: 'Third' },
]);
</script>
