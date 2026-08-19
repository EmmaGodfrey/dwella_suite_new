<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Bloodhound (Suggestion Engine)</h5>
        <span>Bloodhound offers advanced functionalities such as prefetching and backfilling with remote data.</span>
      </div>
      <div class="card-body">
        <div id="bloodhound">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead
                  :items="list"
                  class="form-control typeahead form-control"
                  :placeholder="options.placeholder"
                  @onInput="onInput"
                  @onBlur="onBlur"
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
import { options, list, onInput, onBlur } from '~/composables/commen/typeaheadview';
</script>
