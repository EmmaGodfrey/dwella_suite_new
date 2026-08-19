<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Additional content</h5>
        <span>Alerts can also contain additional HTML elements like headings, paragraphs and dividers.</span>
      </div>
      <div class="card-body">
        <div class="alert alert-primary" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-secondary" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-success" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-danger" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-info" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-light" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
        <div class="alert alert-dark" role="alert">
          <h4 class="alert-heading">{{ done }}</h4>
          <p>{{ desc }}</p>
          <hr />
          <p class="mb-0">{{ content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
const done = ref<string>('Well done!');
const desc = ref<string>(
  'Aww yeah, you successfully read this important alert message. This example text is going to run a bit longer so that you can see how spacing within an alert works with this kind of content.',
);
const content = ref<string>('Whenever you need to, be sure to use margin utilities to keep things nice and tidy.');
</script>
