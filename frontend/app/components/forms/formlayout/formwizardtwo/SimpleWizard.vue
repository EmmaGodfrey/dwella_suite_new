<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Form Wizard And Validation</h5>
        <span>Validation Step Form Wizard</span>
      </div>
      <div class="card-body">
        <ClientOnly>
          <form @submit.prevent="onSubmit">
            <div class="wizard-tabs">
              <button v-for="step in totalSteps" :key="step" type="button" :class="['wizard-tab', { active: currentStep === step }]" @click="goToStep(step)">
                <span class="step-title">{{ stepTitles[step - 1] }}</span>
              </button>
            </div>

            <div v-if="currentStep === 1" class="wizard-step">
              <div class="col-xs-12">
                <div class="col-md-12">
                  <div class="mb-3">
                    <label class="control-label">First Name</label>
                    <input class="form-control" type="text" placeholder="Johan" required />
                  </div>
                  <div class="mb-3">
                    <label class="control-label">Last Name</label>
                    <input class="form-control" type="text" placeholder="Deo" required />
                  </div>
                </div>
              </div>
              <div class="mt-5">
                <button type="button" class="btn btn-next" @click="nextStep">Next</button>
              </div>
            </div>

            <div v-if="currentStep === 2" class="wizard-step">
              <div class="col-xs-12">
                <div class="col-md-12">
                  <div class="mb-3">
                    <label class="control-label">Email</label>
                    <input class="form-control" type="text" placeholder="name@example.com" required />
                  </div>
                  <div class="mb-3">
                    <label class="control-label">Password</label>
                    <input class="form-control" type="password" placeholder="Password" required />
                  </div>
                </div>
              </div>
              <div class="mt-5">
                <button type="button" class="btn btn-back me-2" @click="prevStep">Back</button>
                <button type="button" class="btn btn-next" @click="nextStep">Next</button>
              </div>
            </div>

            <div v-if="currentStep === 3" class="wizard-step">
              <div class="col-xs-12">
                <div class="col-md-12">
                  <div class="mb-3">
                    <label class="control-label">Birth date</label>
                    <input class="form-control" type="date" required />
                  </div>
                  <div class="mb-3">
                    <label class="control-label">Have Passport</label>
                    <input class="form-control" type="text" placeholder="yes/No" required />
                  </div>
                </div>
              </div>
              <div class="mt-5">
                <button type="button" class="btn btn-back me-2" @click="prevStep">Back</button>
                <button type="button" class="btn btn-next" @click="nextStep">Next</button>
              </div>
            </div>

            <div v-if="currentStep === 4" class="wizard-step">
              <div class="col-xs-12">
                <div class="col-md-12">
                  <div class="mb-3">
                    <label class="control-label">State</label>
                    <input class="form-control mt-1" type="text" placeholder="State" required />
                  </div>
                  <div class="mb-3">
                    <label class="control-label">City</label>
                    <input class="form-control mt-1" type="text" placeholder="City" required />
                  </div>
                </div>
              </div>
              <div class="mt-5">
                <button type="button" class="btn btn-back me-2" @click="prevStep">Back</button>
                <button type="submit" class="btn btn-submit">Submit</button>
              </div>
            </div>
          </form>
        </ClientOnly>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useForm } from 'vee-validate';
import * as yup from 'yup';

const currentStep = ref<number>(1);
const totalSteps = 4;
const stepTitles = ['Step 1', 'Step 2', 'Step 3', 'Step 4'];
const formSubmitted = ref(false);

const { handleSubmit, values: form } = useForm({
  initialValues: {
    step1: {},
    step2: {},
    step3: [],
  },
  validationSchema: yup.object({
    step1: yup.object().required(),
    step2: yup.object().required(),
    step3: yup.array().min(1, 'At least 1 image required'),
  }),
});

const nextStep = () => {
  if (currentStep.value < totalSteps) currentStep.value++;
};
const prevStep = () => {
  if (currentStep.value > 1) currentStep.value--;
};
const goToStep = (step: number) => {
  if (step >= 1 && step <= totalSteps) currentStep.value = step;
};

const onSubmit = handleSubmit(formValues => {
  formSubmitted.value = true;

  currentStep.value = 1;
});
</script>
