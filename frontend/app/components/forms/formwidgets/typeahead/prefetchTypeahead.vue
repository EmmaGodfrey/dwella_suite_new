<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Prefetch</h5>
        <span>Prefetched data is fetched and processed on initialization</span>
      </div>
      <div class="card-body">
        <div id="prefetch">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead :items="list" class="form-control typeahead form-control" @onInput="onInput" @onBlur="onBlur" placeholder="Countries" :minInputLength="options.minInputLength"
              /></client-only>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { options, list, onInput, onBlur } from '~/composables/commen/prefetchtypeahead';
</script>
