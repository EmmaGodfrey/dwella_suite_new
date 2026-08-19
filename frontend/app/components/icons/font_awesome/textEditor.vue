<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5 class="m-b-0">Text Editor Icons</h5>
      </div>
      <div class="card-body">
        <div class="row icon-lists">
          <div class="col-sm-6 col-md-4 col-xl-3" v-for="(texteditor, index) in texteditorIcons" :key="index" v-on:click="iconBar(texteditor.name)">
            <i :class="'fa fa-' + texteditor.name"></i>{{ texteditor.name }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const texteditorIcons = ref([
  { name: 'align-center' },
  { name: 'align-justify' },
  { name: 'align-left' },
  { name: 'align-right' },
  { name: 'bold' },
  { name: 'chain' },
  { name: 'chain-broken' },
  { name: 'clipboard' },
  { name: 'columns' },
  { name: 'copy' },
  { name: 'cut' },
  { name: 'dedent' },
  { name: 'eraser' },
  { name: 'file' },
  { name: 'file-o' },
  { name: 'file-text' },
  { name: 'file-text-o' },
  { name: 'files-o' },
  { name: 'floppy-o' },
  { name: 'font' },
  { name: 'header' },
  { name: 'indent' },
  { name: 'italic' },
  { name: 'link' },
  { name: 'list' },
  { name: 'list-alt' },
  { name: 'list-ol' },
  { name: 'list-ul' },
  { name: 'outdent' },
  { name: 'paperclip' },
  { name: 'paragraph' },
  { name: 'paste' },
  { name: 'repeat' },
  { name: 'rotate-left' },
  { name: 'rotate-right' },
  { name: 'save' },
  { name: 'scissors' },
  { name: 'strikethrough' },
  { name: 'subscript' },
  { name: 'superscript' },
  { name: 'table' },
  { name: 'text-height' },
  { name: 'text-width' },
  { name: 'th' },
  { name: 'th-large' },
  { name: 'th-list' },
  { name: 'underline' },
  { name: 'undo' },
  { name: 'unlink' },
]);
const emit = defineEmits(['selected']);

function iconBar(icon: string) {
  emit('selected', icon);
}
</script>

<style lang="scss" scoped>
@import '~/assets/scss/animate.scss';
</style>
