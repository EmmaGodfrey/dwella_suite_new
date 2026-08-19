import { defineStore, acceptHMRUpdate } from 'pinia'
import type { 
  Amenity, 
  AmenityCategory, 
  AmenityCreateInput, 
  AmenityUpdateInput,
  CategoryCreateInput,
  CategoryUpdateInput,
  AmenitiesListParams,
  CategoriesListParams 
} from '../types/amenity'
import type { PaginatedResponse } from '../types/api'

export const useAmenitiesStore = defineStore('amenities', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any
  
  const amenities = ref<Amenity[]>([])
  const categories = ref<AmenityCategory[]>([])
  
  const amenitiesPagination = ref({
    currentPage: 1,
    lastPage: 1,
    perPage: 10,
    total: 0,
    from: 0,
    to: 0,
  })

  const categoriesPagination = ref({
    currentPage: 1,
    lastPage: 1,
    perPage: 10,
    total: 0,
    from: 0,
    to: 0,
  })

  // Amenities
  async function fetchAmenities(params: AmenitiesListParams = {}) {
    const response = await $api.get('/admin/amenities', { params })
    
    if (response.success && response.data) {
      // Handle both paginated response and direct array
      if (Array.isArray(response.data)) {
        amenities.value = response.data
        amenitiesPagination.value = {
          currentPage: 1,
          lastPage: 1,
          perPage: response.data.length,
          total: response.data.length,
          from: 1,
          to: response.data.length,
        }
      } else {
        amenities.value = response.data.data || []
        amenitiesPagination.value = {
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

  async function createAmenity(data: AmenityCreateInput) {
    const response = await $api.post('/admin/amenities', data)
    return response
  }

  async function updateAmenity(id: number, data: AmenityUpdateInput) {
    const response = await $api.put(`/admin/amenities/${id}`, data)
    return response
  }

  async function deleteAmenity(id: number) {
    const response = await $api.delete(`/admin/amenities/${id}`)
    return response
  }

  // Categories
  async function fetchCategories(params: CategoriesListParams = {}) {
    const response = await $api.get('/admin/amenities/categories', { params })
    
    if (response.success && response.data) {
      // Handle both paginated response and direct array
      if (Array.isArray(response.data)) {
        categories.value = response.data
        categoriesPagination.value = {
          currentPage: 1,
          lastPage: 1,
          perPage: response.data.length,
          total: response.data.length,
          from: 1,
          to: response.data.length,
        }
      } else {
        categories.value = response.data.data || []
        categoriesPagination.value = {
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

  async function createCategory(data: CategoryCreateInput) {
    const response = await $api.post('/admin/amenities/categories', data)
    return response
  }

  async function updateCategory(id: number, data: CategoryUpdateInput) {
    const response = await $api.put(`/admin/amenities/categories/${id}`, data)
    return response
  }

  async function deleteCategory(id: number) {
    const response = await $api.delete(`/admin/amenities/categories/${id}`)
    return response
  }

  return {
    amenities,
    categories,
    amenitiesPagination,
    categoriesPagination,
    fetchAmenities,
    createAmenity,
    updateAmenity,
    deleteAmenity,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAmenitiesStore, import.meta.hot))
}
