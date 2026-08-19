<template>
  <TheBreadcrumbs main="Editors" title="CK Editor" />
  <div class="container-fluid">
    <div class="row">
      <div class="col-md-12">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title">CK Editor</h5>
          </div>
          <div class="card-body">
            <ClientOnly>
              <component :is="CkEditorComponent" :editor="ClassicEditor" v-model="editorData" />
            </ClientOnly>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, shallowRef, onMounted } from 'vue';

useHead({
  title: 'CK Editor | Cion - Premium Nuxt Admin Template',
});

const CkEditorComponent = shallowRef();
const ClassicEditor = shallowRef();
const editorData = ref<string>(
  "<p>Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.</p>",
);

onMounted(async () => {
  const { default: CKEditor } = await import('@ckeditor/ckeditor5-vue');
  const { default: Classic } = await import('@ckeditor/ckeditor5-build-classic');
  CkEditorComponent.value = CKEditor.component;
  ClassicEditor.value = Classic;
});
</script>
