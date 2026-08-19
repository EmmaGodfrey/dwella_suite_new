<template>
  <div class="card">
    <div class="card-header pb-0">
      <h4>Tooltips</h4>
      <span class="mt-2"
        >If your form layout allows it, you can swap the <code class="text-danger">.{valid|invalid}-feedback</code> classes for <code class="text-danger">.{valid|invalid}-tooltip</code> classes to
        display validation feedback in a styled tooltip. Be sure to have a parent with <code class="text-danger">position: relative</code> on it for tooltip positioning. In the example below, our
        column classes have this already, but your project may require an alternative setup.</span
      >
    </div>
    <div class="card-body">
      <form class="row g-3 needs-validation" novalidate @submit.prevent="onCustomSubmit">
        <div class="col-md-4 position-relative">
          <label class="form-label" for="validationTooltip01">First name</label>
          <input
            type="text"
            class="form-control"
            v-bind:class="Submitted ? (inputss.firstname.errorMessage.length ? 'is-invalid' : 'is-valid') : ''"
            id="name"
            placeholder="Your name"
            v-model="inputss.firstname.data"
          />
          <div class="invalid-tooltip" v-if="inputss.firstname.errorMessage.length">{{ inputss.firstname.errorMessage }}</div>
          <div class="valid-tooltip" v-else>Looks Good!</div>
        </div>
        <div class="col-md-4 position-relative">
          <label class="form-label" for="validationTooltip02">Last name</label>
          <input
            class="form-control"
            type="text"
            v-bind:class="Submitted ? (inputss.lastname.errorMessage.length ? 'is-invalid' : 'is-valid') : ''"
            id="name"
            placeholder="Your name"
            v-model="inputss.lastname.data"
          />
          <div class="invalid-tooltip" v-if="inputss.lastname.errorMessage.length">{{ inputss.lastname.errorMessage }}</div>
          <div class="valid-tooltip" v-else>Looks Good!</div>
        </div>
        <div class="col-md-4 position-relative">
          <label class="form-label" for="validationTooltipUsername">Username</label>
          <div class="input-group has-validation">
            <span class="input-group-text" id="validationTooltipUsernamePrepend">@</span>
            <input
              class="form-control"
              id="validationCustomUsername"
              type="text"
              v-bind:class="Submitted ? (inputss.username.errorMessage.length ? 'is-invalid' : 'is-valid') : ''"
              placeholder="Username"
              v-model="inputss.username.data"
            />
            <div class="invalid-tooltip" v-if="inputss.username.errorMessage.length">{{ inputss.username.errorMessage }}</div>
            <div class="valid-tooltip" v-else>Looks Good!</div>
          </div>
        </div>
        <div class="col-md-6 position-relative">
          <label class="form-label" for="validationTooltip03">City</label>
          <input
            class="form-control"
            id="validationCustom03"
            type="text"
            v-bind:class="Submitted ? (inputss.city.errorMessage.length ? 'is-invalid' : 'is-valid') : ''"
            placeholder="City"
            required
            v-model="inputss.city.data"
          />
          <div class="invalid-tooltip" v-if="inputss.city.errorMessage.length">{{ inputss.city.errorMessage }}</div>
          <div class="valid-tooltip" v-else>Looks Good!</div>
        </div>
        <div class="col-md-3 position-relative">
          <label class="form-label" for="validationTooltip04">State</label>
          <select class="form-select" id="validationCustom04" v-bind:class="Submitted ? (inputss.state.errorMessage.length ? 'is-invalid' : 'is-valid') : ''" v-model="inputss.state.data" required>
            <option selected disabled value="">Choose...</option>
            <option v-for="(value, index) in optionValues" :value="value" :key="value + index">{{ value }}</option>
          </select>
          <div class="invalid-tooltip" v-if="inputss.state.errorMessage.length">{{ inputss.state.errorMessage }}</div>
          <div class="valid-tooltip" v-else>Looks Good!</div>
        </div>
        <div class="col-md-3 position-relative">
          <label class="form-label" for="validationTooltip05">Zip</label>
          <input
            class="form-control"
            id="validationCustom05"
            type="text"
            v-bind:class="Submitted ? (inputss.zip.errorMessage.length ? 'is-invalid' : 'is-valid') : ''"
            v-model="inputss.zip.data"
            placeholder="Zip"
            required
          />
          <div class="invalid-tooltip" v-if="inputss.zip.errorMessage.length">{{ inputss.zip.errorMessage }}</div>
          <div class="valid-tooltip" v-else>Looks Good!</div>
        </div>
        <div class="col-12">
          <button class="btn btn-primary" type="submit">Submit form</button>
        </div>
      </form>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { onCustomSubmit, inputss, Submitted, optionValues } from '~/composables/commen/validationForm';
</script>
