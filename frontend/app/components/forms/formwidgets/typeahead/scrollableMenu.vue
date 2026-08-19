<template>
  <div class="col-sm-12 col-md-6">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Scrollable Dropdown Menu</h5>
        <span>Dataset shows in scrollable dropdown menu.</span>
      </div>
      <div class="card-body">
        <div id="scrollable-dropdown-menu">
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
