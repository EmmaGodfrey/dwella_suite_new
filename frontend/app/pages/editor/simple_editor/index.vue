<template>
  <TheBreadcrumbs main="Editor" title="Simple Editor" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title">Simple Editor</h5>
          </div>
          <div class="card-body">
            <quill-editor v-model:value="state.content" :options="state.editorOption" @change="onEditorChange($event)" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { reactive } from 'vue';

useHead({
  title: 'Simple Editor | Cion - Premium Nuxt Admin Template',
});
const state = reactive({
  content: '<h1>Some initial content</h1>',
  _content: '',
  editorOption: {
    placeholder: 'core',
  },
  disabled: false,
});
const onEditorChange = (html: string) => {
  state._content = html;
};
setTimeout(() => {
  state.disabled = true;
}, 2000);
</script>
