import { defineStore, acceptHMRUpdate } from 'pinia'
import type { Application, ApplicationStatistics, ApplicationsListParams } from '../types/application'

export const useApplicationsStore = defineStore('applications', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const applications = ref<Application[]>([])
  const statistics = ref<ApplicationStatistics>({ total: 0, new: 0, contacted: 0, accepted: 0, declined: 0 })
  const pagination = ref({ currentPage: 1, lastPage: 1, perPage: 10, total: 0, from: 0, to: 0 })

  async function fetchApplications(params: ApplicationsListParams = {}) {
    const response = await $api.get('/admin/applications', { params })
    if (response.success && response.data) {
      if (Array.isArray(response.data)) {
        applications.value = response.data
        pagination.value = { currentPage: 1, lastPage: 1, perPage: response.data.length, total: response.data.length, from: 1, to: response.data.length }
      } else {
        applications.value = response.data.data || []
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

  async function fetchApplication(id: number) {
    return await $api.get(`/admin/applications/${id}`)
  }

  async function fetchStatistics() {
    const response = await $api.get('/admin/applications/statistics')
    if (response.success && response.data) statistics.value = response.data
    return response
  }

  return { applications, statistics, pagination, fetchApplications, fetchApplication, fetchStatistics }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useApplicationsStore, import.meta.hot))
}
