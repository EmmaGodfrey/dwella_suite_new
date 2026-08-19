import { defineStore, acceptHMRUpdate } from 'pinia'

export interface DashboardOverview {
  total_users: number
  total_listings: number
  total_organizations: number
  total_revenue: number
  active_subscriptions: number
  pending_verifications: number
  pending_listings: number
  total_applications: number
  [key: string]: any
}

export interface ActivityItem {
  id: number
  type: string
  description: string
  created_at: string
  user?: { id: number; full_name: string; email: string }
  [key: string]: any
}

export interface TrendPoint {
  label: string
  value: number
  [key: string]: any
}

export const useAdminDashboardStore = defineStore('adminDashboard', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const overview = ref<DashboardOverview | null>(null)
  const activities = ref<ActivityItem[]>([])
  const revenueTrends = ref<TrendPoint[]>([])
  const listingsTrends = ref<TrendPoint[]>([])
  const isLoading = ref(false)

  async function fetchOverview() {
    const response = await $api.get('/admin/dashboard/overview')
    if (response.success && response.data) {
      overview.value = response.data
    }
    return response
  }

  async function fetchActivities() {
    const response = await $api.get('/admin/dashboard/activities')
    if (response.success && response.data) {
      activities.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function fetchRevenueTrends() {
    const response = await $api.get('/admin/dashboard/revenue-trends')
    if (response.success && response.data) {
      revenueTrends.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function fetchListingsTrends() {
    const response = await $api.get('/admin/dashboard/listings-trends')
    if (response.success && response.data) {
      listingsTrends.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function fetchAll() {
    isLoading.value = true
    await Promise.allSettled([
      fetchOverview(),
      fetchActivities(),
      fetchRevenueTrends(),
      fetchListingsTrends(),
    ])
    isLoading.value = false
  }

  return {
    overview,
    activities,
    revenueTrends,
    listingsTrends,
    isLoading,
    fetchOverview,
    fetchActivities,
    fetchRevenueTrends,
    fetchListingsTrends,
    fetchAll,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAdminDashboardStore, import.meta.hot))
}
