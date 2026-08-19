<template>
  <div class="container-fluid p-0">
    <div class="row">
      <div class="col-12">
        <div class="login-card">
          <div></div>
          <form class="theme-form login-form" @submit.prevent="handleLogin">
            <h4>Login</h4>
            <h6>Welcome back! Log in to your account.</h6>
            
            <div v-if="formErrors.general" class="alert alert-danger">
              {{ formErrors.general }}
            </div>
            
            <div class="form-group">
              <label>Email Address</label>
              <div class="input-group">
                <span class="input-group-text"><i class="icon-email"></i></span>
                <input 
                  v-model="form.email" 
                  class="form-control" 
                  :class="{ 'is-invalid': formErrors.email }"
                  type="email" 
                  placeholder="admin@dwella.com" 
                />
              </div>
              <div v-if="formErrors.email" class="invalid-feedback d-block">
                {{ formErrors.email }}
              </div>
            </div>
            
            <div class="form-group">
              <label>Password</label>
              <div class="input-group">
                <span class="input-group-text"><i class="icon-lock"></i></span>
                <input 
                  v-model="form.password" 
                  :type="showPasswordField ? 'text' : 'password'" 
                  class="form-control"
                  :class="{ 'is-invalid': formErrors.password }"
                  placeholder="*********" 
                />
                <div class="show-hide">
                  <span class="show" @click="showPasswordField = !showPasswordField"></span>
                </div>
              </div>
              <div v-if="formErrors.password" class="invalid-feedback d-block">
                {{ formErrors.password }}
              </div>
            </div>
            
            <div class="form-group">
              <button 
                class="btn btn-primary btn-block w-100" 
                type="submit"
                :disabled="isLoading"
              >
                <span v-if="isLoading">
                  <span class="spinner-border spinner-border-sm me-2"></span>
                  Signing in...
                </span>
                <span v-else>Sign in</span>
              </button>
            </div>
            
            <p class="text-muted mt-3 mb-0">
              Default credentials: admin@dwella.com / Admin@123
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
  name: 'login',
  path: '/login',
  layout: 'custom' as any,
  middleware: 'guest',
  public: true,
  requiresAuth: false,
})

const authStore = useAuthStore()

const form = ref({
  email: '',
  password: '',
})

const formErrors = ref<Record<string, string>>({})
const showPasswordField = ref(false)
const isLoading = ref(false)

const handleLogin = async () => {
  formErrors.value = {}
  isLoading.value = true

  try {
    const response = await authStore.login(form.value)
    
    if (response.success) {
      toast.success(response.message || 'Login successful')
      await nextTick()
      await navigateTo('/dashboard', { replace: true })
    } else {
      if (response.errors) {
        Object.keys(response.errors).forEach(key => {
          formErrors.value[key] = response.errors![key][0]
        })
      } else {
        formErrors.value.general = response.message || 'Login failed'
      }
      toast.error(response.message || 'Login failed')
    }
  } catch (error: any) {
    formErrors.value.general = error.message || 'An error occurred during login'
    toast.error('An error occurred during login')
  } finally {
    isLoading.value = false
  }
}
</script>
