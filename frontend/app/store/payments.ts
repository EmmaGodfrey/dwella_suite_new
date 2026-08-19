import { defineStore, acceptHMRUpdate } from 'pinia'
import type { Payment, PaymentStatistics, PaymentAnalyticsPoint, PaymentsListParams } from '../types/payment'

export const usePaymentsStore = defineStore('payments', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const payments = ref<Payment[]>([])
  const statistics = ref<PaymentStatistics>({ total: 0, successful: 0, pending: 0, failed: 0, refunded: 0, total_revenue: 0 })
  const analyticsData = ref<PaymentAnalyticsPoint[]>([])
  const pagination = ref({ currentPage: 1, lastPage: 1, perPage: 15, total: 0, from: 0, to: 0 })

  async function fetchPayments(params: PaymentsListParams = {}) {
    const response = await $api.get('/admin/payments', { params })
    if (response.success && response.data) {
      if (Array.isArray(response.data)) {
        payments.value = response.data
        pagination.value = { currentPage: 1, lastPage: 1, perPage: response.data.length, total: response.data.length, from: 1, to: response.data.length }
      } else {
        payments.value = response.data.data || []
        pagination.value = {
          currentPage: response.data.current_page || 1,
          lastPage: response.data.last_page || 1,
          perPage: response.data.per_page || 15,
          total: response.data.total || 0,
          from: response.data.from || 0,
          to: response.data.to || 0,
        }
      }
    }
    return response
  }

  async function fetchPayment(id: number) {
    return await $api.get(`/admin/payments/${id}`)
  }

  async function fetchStatistics() {
    const response = await $api.get('/admin/payments/statistics')
    if (response.success && response.data) statistics.value = response.data
    return response
  }

  async function fetchAnalytics(params: { from?: string; to?: string; group_by?: string } = {}) {
    const response = await $api.get('/admin/payments/analytics', { params })
    if (response.success && response.data) {
      analyticsData.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  return { payments, statistics, analyticsData, pagination, fetchPayments, fetchPayment, fetchStatistics, fetchAnalytics }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(usePaymentsStore, import.meta.hot))
}
