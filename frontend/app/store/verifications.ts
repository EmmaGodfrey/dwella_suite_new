import { defineStore, acceptHMRUpdate } from 'pinia'
import type { Verification, VerificationPlan, VerificationStatistics, VerificationsListParams, VerificationPlanInput } from '../types/verification'

export const useVerificationsStore = defineStore('verifications', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const verifications = ref<Verification[]>([])
  const plans = ref<VerificationPlan[]>([])
  const statistics = ref<VerificationStatistics>({ total: 0, pending: 0, approved: 0, rejected: 0, revoked: 0 })
  const pagination = ref({ currentPage: 1, lastPage: 1, perPage: 10, total: 0, from: 0, to: 0 })

  async function fetchVerifications(params: VerificationsListParams = {}) {
    const response = await $api.get('/admin/verifications', { params })
    if (response.success && response.data) {
      if (Array.isArray(response.data)) {
        verifications.value = response.data
        pagination.value = { currentPage: 1, lastPage: 1, perPage: response.data.length, total: response.data.length, from: 1, to: response.data.length }
      } else {
        verifications.value = response.data.data || []
        pagination.value = {
          currentPage: response.data.current_page || 1,
          lastPage: response.data.last_page || 1,
          perPage: response.data.per_page || 10,
          total: response.data.total || 0,
          from: response.data.from || 0,
          to: response.data.to || 0,
        }
      }
    }
    return response
  }

  async function fetchVerification(id: number) {
    return await $api.get(`/admin/verifications/${id}`)
  }

  async function fetchStatistics() {
    const response = await $api.get('/admin/verifications/statistics')
    if (response.success && response.data) statistics.value = response.data
    return response
  }

  async function approveVerification(id: number) {
    return await $api.post(`/admin/verifications/${id}/approve`)
  }

  async function rejectVerification(id: number, reason: string) {
    return await $api.post(`/admin/verifications/${id}/reject`, { reason })
  }

  async function revokeVerification(id: number, reason: string) {
    return await $api.post(`/admin/verifications/${id}/revoke`, { reason })
  }

  // Plans
  async function fetchPlans() {
    const response = await $api.get('/admin/verifications/plans')
    if (response.success && response.data) {
      plans.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function createPlan(data: VerificationPlanInput) {
    return await $api.post('/admin/verifications/plans', data)
  }

  async function updatePlan(id: number, data: Partial<VerificationPlanInput>) {
    return await $api.put(`/admin/verifications/plans/${id}`, data)
  }

  async function deletePlan(id: number) {
    return await $api.delete(`/admin/verifications/plans/${id}`)
  }

  return {
    verifications, plans, statistics, pagination,
    fetchVerifications, fetchVerification, fetchStatistics,
    approveVerification, rejectVerification, revokeVerification,
    fetchPlans, createPlan, updatePlan, deletePlan,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useVerificationsStore, import.meta.hot))
}
