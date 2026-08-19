<template>
  <div class="container-fluid p-0">
    <div class="row">
      <div class="col-12">
        <div class="login-card">
          <div></div>
          <form class="theme-form login-form" @submit.prevent="handleSubmit">
            <h4>Reset Password</h4>
            <h6>Enter your new password below.</h6>

            <div v-if="success" class="alert alert-success">
              Password reset! <NuxtLink to="/login" class="link-primary">Login here.</NuxtLink>
            </div>

            <div v-if="errorMsg" class="alert alert-danger">{{ errorMsg }}</div>

            <template v-if="!success">
              <div class="form-group">
                <label>New Password</label>
                <div class="input-group">
                  <span class="input-group-text"><i class="icon-lock"></i></span>
                  <input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    class="form-control"
                    :class="{ 'is-invalid': fieldError('password') }"
                    placeholder="••••••••"
                    required
                  />
                  <div class="show-hide">
                    <span class="show" @click="showPassword = !showPassword"></span>
                  </div>
                </div>
                <div v-if="fieldError('password')" class="invalid-feedback d-block">
                  {{ fieldError('password') }}
                </div>
              </div>

              <div class="form-group">
                <label>Confirm Password</label>
                <div class="input-group">
                  <span class="input-group-text"><i class="icon-lock"></i></span>
                  <input
                    v-model="form.password_confirmation"
                    :type="showPassword ? 'text' : 'password'"
                    class="form-control"
                    :class="{ 'is-invalid': fieldError('password_confirmation') }"
                    placeholder="••••••••"
                    required
                  />
                </div>
                <div v-if="fieldError('password_confirmation')" class="invalid-feedback d-block">
                  {{ fieldError('password_confirmation') }}
                </div>
              </div>

              <div class="form-group">
                <button class="btn btn-primary btn-block w-100" type="submit" :disabled="isLoading">
                  <span v-if="isLoading">
                    <span class="spinner-border spinner-border-sm me-2"></span>Resetting...
                  </span>
                  <span v-else>Reset Password</span>
                </button>
              </div>
            </template>

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
  name: 'reset-password',
  path: '/reset-password',
  layout: 'custom' as any,
  middleware: 'guest',
  public: true,
  requiresAuth: false,
})

const route = useRoute()
const { $api } = useNuxtApp() as any

const form = ref({
  token: (route.query.token as string) || '',
  email: (route.query.email as string) || '',
  password: '',
  password_confirmation: '',
})

const showPassword = ref(false)
const isLoading = ref(false)
const success = ref(false)
const errorMsg = ref('')
const fieldErrors = ref<Record<string, string[]>>({})

const fieldError = (key: string) => fieldErrors.value[key]?.[0] ?? ''

const handleSubmit = async () => {
  errorMsg.value = ''
  fieldErrors.value = {}
  isLoading.value = true

  try {
    const response = await $api.post('/auth/reset-password', form.value)

    if (response.success) {
      success.value = true
      toast.success(response.message || 'Password reset successfully!')
    } else {
      if (response.errors) {
        fieldErrors.value = response.errors
      } else {
        errorMsg.value = response.message || 'Failed to reset password.'
      }
      toast.error(response.message || 'Reset failed.')
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'An error occurred.'
    toast.error(errorMsg.value)
  } finally {
    isLoading.value = false
  }
}
</script>
