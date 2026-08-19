import { defineStore, acceptHMRUpdate } from 'pinia'
import type { Listing, ListingsListParams, ListingStatistics, CreateListingInput } from '../types/listing'
import type { PaginatedResponse } from '../types/api'

export const useListingsStore = defineStore('listings', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any
  
  const listings = ref<Listing[]>([])
  const statistics = ref<ListingStatistics>({
    total: 0,
    published: 0,
    pending: 0,
    draft: 0,
    rejected: 0,
    archived: 0,
  })
  
  const pagination = ref({
    currentPage: 1,
    lastPage: 1,
    perPage: 10,
    total: 0,
    from: 0,
    to: 0,
  })

  async function fetchListings(params: ListingsListParams = {}) {
    const response = await $api.get('/admin/listings', { params })
    
    if (response.success && response.data) {
      // Handle both paginated response and direct array
      if (Array.isArray(response.data)) {
        // Direct array response (fallback)
        listings.value = response.data
        pagination.value = {
          currentPage: 1,
          lastPage: 1,
          perPage: response.data.length,
          total: response.data.length,
          from: 1,
          to: response.data.length,
        }
      } else {
        // Paginated response
        listings.value = response.data.data || []
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

  async function fetchListing(id: number) {
    const response = await $api.get(`/admin/listings/${id}`)
    return response
  }

  async function approveListing(id: number) {
    const response = await $api.post(`/admin/listings/${id}/approve`)
    return response
  }

  async function rejectListing(id: number, reason: string) {
    const response = await $api.post(`/admin/listings/${id}/reject`, { reason })
    return response
  }

  async function publishListing(id: number) {
    const response = await $api.post(`/admin/listings/${id}/publish`)
    return response
  }

  async function archiveListing(id: number) {
    const response = await $api.post(`/admin/listings/${id}/archive`)
    return response
  }

  async function deleteListing(id: number) {
    const response = await $api.delete(`/admin/listings/${id}`)
    return response
  }

  async function fetchStatistics() {
    const response = await $api.get('/admin/listings/statistics')
    if (response.success && response.data) {
      statistics.value = response.data
    }
    return response
  }

  async function createListing(data: CreateListingInput) {
    // If images are provided, send as FormData
    if (data.images && data.images.length > 0) {
      const formData = new FormData()
      
      // Add all other fields
      Object.keys(data).forEach((key) => {
        if (key === 'images') return
        if (key === 'amenity_ids' && data.amenity_ids) {
          data.amenity_ids.forEach((id) => formData.append('amenity_ids[]', String(id)))
        } else if (data[key as keyof CreateListingInput] !== undefined) {
          formData.append(key, String(data[key as keyof CreateListingInput]))
        }
      })
      
      // Add images
      data.images.forEach((image) => {
        formData.append('images[]', image)
      })
      
      const response = await $api.post('/admin/listings', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return response
    }
    
    // Otherwise send as JSON
    const response = await $api.post('/admin/listings', data)
    return response
  }

  return {
    listings,
    statistics,
    pagination,
    fetchListings,
    fetchListing,
    createListing,
    approveListing,
    rejectListing,
    publishListing,
    archiveListing,
    deleteListing,
    fetchStatistics,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useListingsStore, import.meta.hot))
}
