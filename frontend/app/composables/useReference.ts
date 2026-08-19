import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'

export const useReference = () => {
  const referenceStore = useReferenceStore()
  const queryClient = useQueryClient()

  // ─── Queries (read, 30-min cache) ──────────────────────────────────────

  const useFetchPropertyTypesQuery = () =>
    useQuery({
      queryKey: ['property-types'],
      queryFn: queryWrap(() => referenceStore.fetchPropertyTypes(), { showToast: false }),
      staleTime: 1000 * 60 * 30,
    })

  const useFetchProvincesQuery = () =>
    useQuery({
      queryKey: ['provinces'],
      queryFn: queryWrap(() => referenceStore.fetchProvinces(), { showToast: false }),
      staleTime: 1000 * 60 * 30,
    })

  const useFetchDistrictsQuery = (provinceId?: Ref<number | undefined>) =>
    useQuery({
      queryKey: ['districts', provinceId],
      queryFn: queryWrap(() => referenceStore.fetchDistricts(provinceId?.value), { showToast: false }),
      enabled: computed(() => !provinceId || !!provinceId.value),
      staleTime: 1000 * 60 * 30,
    })

  const useFetchConstituenciesQuery = (districtId?: Ref<number | undefined>) =>
    useQuery({
      queryKey: ['constituencies', districtId],
      queryFn: queryWrap(() => referenceStore.fetchConstituencies(districtId?.value), { showToast: false }),
      enabled: computed(() => !districtId || !!districtId.value),
      staleTime: 1000 * 60 * 30,
    })

  const useFetchAmenitiesForSelectQuery = () =>
    useQuery({
      queryKey: ['amenities-select'],
      queryFn: queryWrap(() => referenceStore.fetchAmenitiesForSelect(), { showToast: false }),
      staleTime: 1000 * 60 * 30,
    })

  const useFetchOrganizationsQuery = () =>
    useQuery({
      queryKey: ['organizations'],
      queryFn: queryWrap(() => referenceStore.fetchOrganizations(), { showToast: false }),
      staleTime: 1000 * 60 * 30,
    })

  // ─── Property Type mutations ────────────────────────────────────────────

  const useCreatePropertyTypeMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        (data: { name: string; description?: string }) => referenceStore.createPropertyType(data),
        { successMessage: 'Property type created', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['property-types'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useUpdatePropertyTypeMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, data }: { id: number; data: { name?: string; description?: string } }) =>
          referenceStore.updatePropertyType(id, data),
        { successMessage: 'Property type updated', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['property-types'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useDeletePropertyTypeMutation = () =>
    useMutation({
      mutationFn: mutationWrap(
        (id: number) => referenceStore.deletePropertyType(id),
        { successMessage: 'Property type deleted', showToast: true }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['property-types'] }),
    })

  // ─── Province mutations ─────────────────────────────────────────────────

  const useCreateProvinceMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        (data: { name: string }) => referenceStore.createProvince(data),
        { successMessage: 'Province created', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['provinces'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useUpdateProvinceMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, data }: { id: number; data: { name?: string } }) => referenceStore.updateProvince(id, data),
        { successMessage: 'Province updated', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['provinces'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useDeleteProvinceMutation = () =>
    useMutation({
      mutationFn: mutationWrap(
        (id: number) => referenceStore.deleteProvince(id),
        { successMessage: 'Province deleted', showToast: true }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['provinces'] }),
    })

  // ─── District mutations ─────────────────────────────────────────────────

  const useCreateDistrictMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        (data: { name: string; province_id: number }) => referenceStore.createDistrict(data),
        { successMessage: 'District created', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['districts'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useUpdateDistrictMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, data }: { id: number; data: { name?: string; province_id?: number } }) =>
          referenceStore.updateDistrict(id, data),
        { successMessage: 'District updated', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['districts'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useDeleteDistrictMutation = () =>
    useMutation({
      mutationFn: mutationWrap(
        (id: number) => referenceStore.deleteDistrict(id),
        { successMessage: 'District deleted', showToast: true }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['districts'] }),
    })

  // ─── Constituency mutations ─────────────────────────────────────────────

  const useCreateConstituencyMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        (data: { name: string; district_id: number }) => referenceStore.createConstituency(data),
        { successMessage: 'Constituency created', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['constituencies'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useUpdateConstituencyMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, data }: { id: number; data: { name?: string; district_id?: number } }) =>
          referenceStore.updateConstituency(id, data),
        { successMessage: 'Constituency updated', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['constituencies'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useDeleteConstituencyMutation = () =>
    useMutation({
      mutationFn: mutationWrap(
        (id: number) => referenceStore.deleteConstituency(id),
        { successMessage: 'Constituency deleted', showToast: true }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['constituencies'] }),
    })

  return {
    // Queries
    useFetchPropertyTypesQuery,
    useFetchProvincesQuery,
    useFetchDistrictsQuery,
    useFetchConstituenciesQuery,
    useFetchAmenitiesForSelectQuery,
    useFetchOrganizationsQuery,
    // Property Type mutations
    useCreatePropertyTypeMutation,
    useUpdatePropertyTypeMutation,
    useDeletePropertyTypeMutation,
    // Province mutations
    useCreateProvinceMutation,
    useUpdateProvinceMutation,
    useDeleteProvinceMutation,
    // District mutations
    useCreateDistrictMutation,
    useUpdateDistrictMutation,
    useDeleteDistrictMutation,
    // Constituency mutations
    useCreateConstituencyMutation,
    useUpdateConstituencyMutation,
    useDeleteConstituencyMutation,
  }
}
