<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Clipboard On Paragraph</h5>
      </div>
      <div class="card-body">
        <div class="clipboaard-container">
          <p class="card-description">Copy from Paragraph</p>
          <h6 class="border rounded card-body f-w-300" v-text="paragraph" id="paragraph"></h6>
          <div class="mt-3 text-end">
            <button class="btn btn-primary btn-clipboard" type="button" @click="copyParagraphInput('paragraph')" data-clipboard-action="copy" data-clipboard-target="#clipboardExample3">
              <i class="fa fa-copy"></i> Copy
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const paragraph = ref<string>('Lorem ipsum dolor sit amet, consectetur adipiscing elit,sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.');

function copyParagraphInput(elementId: string) {
  var aux = document.createElement('input');
  let element = document.getElementById(elementId) as HTMLInputElement;
  aux.setAttribute('value', element.innerHTML);
  document.body.appendChild(aux);
  aux.select();
  document.execCommand('copy');
  document.body.removeChild(aux);
  alert('copied');
}
</script>
