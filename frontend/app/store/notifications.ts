import { defineStore, acceptHMRUpdate } from 'pinia'
import type { Notification, NotificationTemplate, BulkPushInput } from '../types/notification'

export const useNotificationsAdminStore = defineStore('notificationsAdmin', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const notifications = ref<Notification[]>([])
  const templates = ref<NotificationTemplate[]>([])
  const pagination = ref({ currentPage: 1, lastPage: 1, perPage: 15, total: 0, from: 0, to: 0 })

  async function fetchNotifications(params: Record<string, any> = {}) {
    const response = await $api.get('/admin/notifications', { params })
    if (response.success && response.data) {
      if (Array.isArray(response.data)) {
        notifications.value = response.data
        pagination.value = { currentPage: 1, lastPage: 1, perPage: response.data.length, total: response.data.length, from: 1, to: response.data.length }
      } else {
        notifications.value = response.data.data || []
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

  async function fetchTemplates() {
    const response = await $api.get('/admin/notifications/templates')
    if (response.success && response.data) {
      templates.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function sendBulkPush(data: BulkPushInput) {
    return await $api.post('/admin/notifications/bulk-push', data)
  }

  return { notifications, templates, pagination, fetchNotifications, fetchTemplates, sendBulkPush }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useNotificationsAdminStore, import.meta.hot))
}
