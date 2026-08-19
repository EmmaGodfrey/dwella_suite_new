<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Clipboard On Text Input</h5>
      </div>
      <div class="card-body">
        <div class="clipboaard-container">
          <p class="card-description">Cut/copy from text input</p>
          <input class="form-control" id="clipboardExample1" v-model="textInput" type="text" placeholder="type some text to copy / cut" ref="text" />
          <div class="mt-3 text-end">
            <button class="btn btn-primary btn-clipboard" type="button" @click="copyTextInput" data-clipboard-action="copy" data-clipboard-target="#clipboardExample1">
              <i class="fa fa-copy"></i> Copy
            </button>
            <button class="btn btn-secondary btn-clipboard-cut ms-1" type="button" data-clipboard-action="cut" data-clipboard-target="#clipboardExample1" @click="cut">
              <i class="fa fa-cut"></i> Cut
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const textInput = ref<string>('');

function copyTextInput() {
  navigator.clipboard.writeText(textInput.value);
  alert('copied');
}
function cut() {
  navigator.clipboard.writeText(textInput.value);
  textInput.value = '';
  alert('cut');
}
</script>
