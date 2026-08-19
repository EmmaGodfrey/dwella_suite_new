<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>RTL Support</h5>
        <span>Dataset shows in Right Side.</span>
      </div>
      <div class="card-body">
        <div id="rtl-support">
          <form class="theme-form">
            <div>
              <client-only>
                <vue3-simple-typeahead
                  :items="list"
                  class="form-control typeahead form-control"
                  dir="rtl"
                  @onInput="onInput"
                  @onBlur="onBlur"
                  placeholder="Countries"
                  :minInputLength="options.minInputLength"
                  :hint="options.hint"
              /></client-only>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { options, onInput, onBlur } from '~/composables/commen/typeaheadview';

interface data {
  placeholder: string;
  minInputLength: number;
}

const list = ref<string[]>(['India', 'USA', 'Australia', 'UEA', 'China']);
</script>
