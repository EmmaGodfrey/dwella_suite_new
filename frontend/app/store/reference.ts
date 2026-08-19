import { defineStore, acceptHMRUpdate } from 'pinia'
import type { PropertyType, Province, District, Constituency, Amenity, Organization } from '../types/listing'

export const useReferenceStore = defineStore('reference', () => {
  const nuxtApp = useNuxtApp()
  const $api = nuxtApp.$api as any

  const propertyTypes = ref<PropertyType[]>([])
  const provinces = ref<Province[]>([])
  const districts = ref<District[]>([])
  const constituencies = ref<Constituency[]>([])
  const amenities = ref<Amenity[]>([])
  const organizations = ref<Organization[]>([])

  // ─── Property Types ──────────────────────────────────────────────────────

  async function fetchPropertyTypes() {
    const response = await $api.get('/admin/reference-data/property-types')
    if (response.success && response.data) {
      propertyTypes.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function createPropertyType(data: { name: string; description?: string }) {
    return await $api.post('/admin/reference-data/property-types', data)
  }

  async function updatePropertyType(id: number, data: { name?: string; description?: string }) {
    return await $api.put(`/admin/reference-data/property-types/${id}`, data)
  }

  async function deletePropertyType(id: number) {
    return await $api.delete(`/admin/reference-data/property-types/${id}`)
  }

  // ─── Provinces ───────────────────────────────────────────────────────────

  async function fetchProvinces() {
    const response = await $api.get('/admin/reference-data/provinces')
    if (response.success && response.data) {
      provinces.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function createProvince(data: { name: string }) {
    return await $api.post('/admin/reference-data/provinces', data)
  }

  async function updateProvince(id: number, data: { name?: string }) {
    return await $api.put(`/admin/reference-data/provinces/${id}`, data)
  }

  async function deleteProvince(id: number) {
    return await $api.delete(`/admin/reference-data/provinces/${id}`)
  }

  // ─── Districts ───────────────────────────────────────────────────────────

  async function fetchDistricts(provinceId?: number) {
    const params = provinceId ? { province_id: provinceId } : {}
    const response = await $api.get('/admin/reference-data/districts', { params })
    if (response.success && response.data) {
      districts.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function createDistrict(data: { name: string; province_id: number }) {
    return await $api.post('/admin/reference-data/districts', data)
  }

  async function updateDistrict(id: number, data: { name?: string; province_id?: number }) {
    return await $api.put(`/admin/reference-data/districts/${id}`, data)
  }

  async function deleteDistrict(id: number) {
    return await $api.delete(`/admin/reference-data/districts/${id}`)
  }

  // ─── Constituencies ──────────────────────────────────────────────────────

  async function fetchConstituencies(districtId?: number) {
    const params = districtId ? { district_id: districtId } : {}
    const response = await $api.get('/admin/reference-data/constituencies', { params })
    if (response.success && response.data) {
      constituencies.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  async function createConstituency(data: { name: string; district_id: number }) {
    return await $api.post('/admin/reference-data/constituencies', data)
  }

  async function updateConstituency(id: number, data: { name?: string; district_id?: number }) {
    return await $api.put(`/admin/reference-data/constituencies/${id}`, data)
  }

  async function deleteConstituency(id: number) {
    return await $api.delete(`/admin/reference-data/constituencies/${id}`)
  }

  // ─── Amenities (select list for forms) ───────────────────────────────────

  async function fetchAmenitiesForSelect() {
    const response = await $api.get('/admin/amenities', { params: { per_page: 1000 } })
    if (response.success && response.data) {
      amenities.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  // ─── Organizations (select list for forms) ────────────────────────────────

  async function fetchOrganizations() {
    const response = await $api.get('/admin/organizations', { params: { per_page: 1000 } })
    if (response.success && response.data) {
      organizations.value = Array.isArray(response.data) ? response.data : response.data.data || []
    }
    return response
  }

  return {
    propertyTypes,
    provinces,
    districts,
    constituencies,
    amenities,
    organizations,
    // Property Types
    fetchPropertyTypes, createPropertyType, updatePropertyType, deletePropertyType,
    // Provinces
    fetchProvinces, createProvince, updateProvince, deleteProvince,
    // Districts
    fetchDistricts, createDistrict, updateDistrict, deleteDistrict,
    // Constituencies
    fetchConstituencies, createConstituency, updateConstituency, deleteConstituency,
    // Select lists
    fetchAmenitiesForSelect,
    fetchOrganizations,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useReferenceStore, import.meta.hot))
}
