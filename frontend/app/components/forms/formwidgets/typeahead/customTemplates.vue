<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Custom Templates</h5>
        <span>Custom templates give you full control over how suggestions get rendered</span>
      </div>
      <div class="card-body">
        <div id="custom-templates">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead
                  :items="list"
                  class="form-control typeahead form-control"
                  @onInput="onInput"
                  @onBlur="onBlur"
                  placeholder="Oscar winners"
                  :minInputLength="options.minInputLength"
              /></client-only>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { options, list, onInput, onBlur } from '~/composables/customTemplates';
</script>
