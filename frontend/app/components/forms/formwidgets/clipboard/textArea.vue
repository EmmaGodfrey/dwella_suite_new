<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Clipboard On Textarea</h5>
      </div>
      <div class="card-body">
        <div class="clipboaard-container">
          <p class="card-description">Cut/copy from textarea</p>
          <textarea class="form-control f-14" id="clipboardExample2" v-model="textArea" rows="1" spellcheck="false">
Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has</textarea
          >
          <div class="mt-3 text-end">
            <button class="btn btn-primary btn-clipboard" type="button" data-clipboard-action="copy" data-clipboard-target="#clipboardExample2" @click="copyTextareaInput">
              <i class="fa fa-copy"></i> Copy
            </button>
            <button class="btn btn-secondary btn-clipboard-cut ms-1" @click="cut" type="button" data-clipboard-action="cut" data-clipboard-target="#clipboardExample2">
              <i class="fa fa-cut"></i> Cut
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const textArea = ref<string>(
  "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has",
);

function copyTextareaInput() {
  navigator.clipboard.writeText(textArea.value);
  alert('copied');
}
function cut() {
  navigator.clipboard.writeText(textArea.value);
  textArea.value = '';
  alert('cut');
}
</script>
