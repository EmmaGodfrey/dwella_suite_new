<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Remote</h5>
        <span>Remote data is only used when the data provided by local and prefetch is insufficient</span>
      </div>
      <div class="card-body">
        <div id="remote">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead
                  :items="remote"
                  class="form-control typeahead form-control"
                  @onInput="onInput"
                  @onBlur="onBlur"
                  placeholder="Choose Option"
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
import { options, remote, onInput, onBlur } from '~/composables/customTemplates';
</script>
