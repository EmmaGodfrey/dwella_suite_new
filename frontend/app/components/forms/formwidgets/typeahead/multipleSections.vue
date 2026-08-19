<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Multiple Sections with Headers</h5>
        <span>Two datasets that are prefetched, stored, and searched on the client. Highlighting is enabled.</span>
      </div>
      <div class="card-body">
        <div id="multiple-datasets">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead
                  :items="multiple"
                  class="form-control typeahead form-control"
                  @onInput="onInput"
                  @onBlur="onBlur"
                  placeholder="NBA and NHL teams"
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
import { options, multiple, onInput, onBlur } from '~/composables/customTemplates';
</script>
