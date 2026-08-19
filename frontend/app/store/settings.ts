import { defineStore, acceptHMRUpdate } from 'pinia'

export const useSettingsStore = defineStore('settings', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const paymentSettings = ref<Record<string, any> | null>(null)

  async function fetchPaymentSettings() {
    const response = await $api.get('/admin/settings/payment')
    if (response.success && response.data) paymentSettings.value = response.data
    return response
  }

  async function updatePaymentSettings(data: Record<string, any>) {
    const response = await $api.put('/admin/settings/payment', data)
    if (response.success && response.data) paymentSettings.value = response.data
    return response
  }

  async function clearCache() {
    return await $api.post('/admin/settings/cache/clear')
  }

  async function sendTestEmail(email: string) {
    return await $api.post('/admin/settings/email/test', { email })
  }

  return { paymentSettings, fetchPaymentSettings, updatePaymentSettings, clearCache, sendTestEmail }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useSettingsStore, import.meta.hot))
}
