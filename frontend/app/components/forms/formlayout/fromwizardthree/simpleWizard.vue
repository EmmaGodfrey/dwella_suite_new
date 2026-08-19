<template>
  <div class="col-sm-12">
    <div class="card">
      <div class="card-header pb-0">
        <h5>Form Wizard with icon</h5>
      </div>
      <div class="card-body">
        <form method="post">
          <ClientOnly>
            <form @submit.prevent="onSubmit">
              <div class="wizard-tabs">
                <button v-for="step in totalSteps" :key="step" type="button" :class="['wizard-tab', { active: currentStep === step }]" @click="goToStep(step)">
                  <i class="wizard-icon" :class="stepIcons[step - 1]"></i>
                  <span class="step-title">{{ stepTitles[step - 1] }}</span>
                </button>
              </div>

              <div v-if="currentStep === 1" class="wizard-step">
                <fieldset>
                  <div class="mb-2">
                    <label for="f1-first-name">First Name</label>
                    <input class="form-control" id="f1-first-name" type="text" name="f1-first-name" placeholder="name@example.com" required />
                  </div>
                  <div class="mb-2">
                    <label for="f1-last-name">Last name</label>
                    <input class="f1-last-name form-control" id="f1-last-name" type="text" name="f1-last-name" placeholder="Last name..." required />
                  </div>
                </fieldset>
                <div class="mt-5">
                  <button type="button" class="btn btn-next" @click="nextStep">Next</button>
                </div>
              </div>

              <div v-if="currentStep === 2" class="wizard-step">
                <fieldset>
                  <div class="mb-2">
                    <label class="control-label" for="f1-email">Email</label>
                    <input class="f1-email form-control" id="f1-email" type="text" placeholder="Email..." required />
                  </div>
                  <div class="mb-2">
                    <label class="control-label" for="f1-password">Password</label>
                    <input class="f1-password form-control" id="f1-password" type="password" placeholder="Password..." required />
                  </div>
                  <div class="mb-2">
                    <label class="control-label" for="f1-repeat-password">Repeat password</label>
                    <input class="f1-repeat-password form-control" id="f1-repeat-password" type="password" placeholder="Repeat password..." required />
                  </div>
                </fieldset>
                <div class="mt-5">
                  <button type="button" class="btn btn-back me-2" @click="prevStep">Back</button>
                  <button type="button" class="btn btn-next" @click="nextStep">Next</button>
                </div>
              </div>

              <div v-if="currentStep === 3" class="wizard-step">
                <fieldset>
                  <div class="mb-2">
                    <label class="control-label">DD</label>
                    <input class="form-control" id="dd" type="number" placeholder="dd" required />
                  </div>
                  <div class="mb-2">
                    <label class="control-label">MM</label>
                    <input class="form-control" id="mm" type="number" placeholder="mm" required />
                  </div>
                  <div class="mb-2">
                    <label class="control-label">YYYY</label>
                    <input class="form-control" id="yyyy" type="number" placeholder="yyyy" required />
                  </div>
                </fieldset>
                <div class="mt-5">
                  <button type="button" class="btn btn-back me-2" @click="prevStep">Back</button>
                  <button type="submit" class="btn btn-submit">Submit</button>
                </div>
              </div>
            </form>
          </ClientOnly>
        </form>
      </div>
    </div>
  </div>
</template>
<script lang="ts" setup>
import { useForm } from 'vee-validate';
import * as yup from 'yup';

const currentStep = ref<number>(1);
const totalSteps = 3;
const stepTitles = ['Registration', 'Email', 'Birth Date'];
const stepIcons = ['fa fa-user ', 'fa fa-key', 'fa fa-twitter'];
const formSubmitted = ref(false);

const { handleSubmit, values: form } = useForm({
  initialValues: {
    registration: {},
    email: {},
    date: [],
  },
  validationSchema: yup.object({
    registration: yup.object().required(),
    email: yup.object().required(),
    date: yup.array().min(1, 'At least 1 image required'),
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
