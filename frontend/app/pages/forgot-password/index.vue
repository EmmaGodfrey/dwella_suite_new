<template>
  <div class="container-fluid p-0">
    <div class="row">
      <div class="col-12">
        <div class="login-card">
          <div></div>
          <form class="theme-form login-form" @submit.prevent="handleSubmit">
            <h4>Forgot Password</h4>
            <h6>Enter your email and we'll send a reset link.</h6>

            <div v-if="success" class="alert alert-success">
              Reset link sent! Check your email inbox.
            </div>

            <div v-if="errorMsg" class="alert alert-danger">{{ errorMsg }}</div>

            <div class="form-group">
              <label>Email Address</label>
              <div class="input-group">
                <span class="input-group-text"><i class="icon-email"></i></span>
                <input
                  v-model="email"
                  type="email"
                  class="form-control"
                  :class="{ 'is-invalid': emailError }"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div v-if="emailError" class="invalid-feedback d-block">{{ emailError }}</div>
            </div>

            <div class="form-group">
              <button class="btn btn-primary btn-block w-100" type="submit" :disabled="isLoading">
                <span v-if="isLoading">
                  <span class="spinner-border spinner-border-sm me-2"></span>Sending...
                </span>
                <span v-else>Send Reset Link</span>
              </button>
            </div>

            <p class="text-center mt-3 mb-0">
              <NuxtLink to="/login" class="link-primary">Back to Login</NuxtLink>
            </p>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { toast } from 'vue3-toastify'

definePageMeta({
  name: 'forgot-password',
  path: '/forgot-password',
  layout: 'custom' as any,
  middleware: 'guest',
  public: true,
  requiresAuth: false,
})

const { $api } = useNuxtApp() as any

const email = ref('')
const emailError = ref('')
const errorMsg = ref('')
const isLoading = ref(false)
const success = ref(false)

const handleSubmit = async () => {
  emailError.value = ''
  errorMsg.value = ''
  isLoading.value = true

  try {
    const response = await $api.post('/auth/forgot-password', { email: email.value })

    if (response.success) {
      success.value = true
      toast.success(response.message || 'Reset link sent!')
    } else {
      if (response.errors?.email) {
        emailError.value = response.errors.email[0]
      } else {
        errorMsg.value = response.message || 'Failed to send reset link.'
      }
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'An error occurred.'
    toast.error(errorMsg.value)
  } finally {
    isLoading.value = false
  }
}
</script>
