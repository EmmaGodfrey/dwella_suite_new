import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'
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

export const useAmenities = () => {
  const amenitiesStore = useAmenitiesStore()
  const queryClient = useQueryClient()

  // Fetch amenities query
  const useFetchAmenitiesQuery = (params: Ref<AmenitiesListParams>) => {
    return useQuery({
      queryKey: ['amenities', params],
      queryFn: queryWrap(
        () => amenitiesStore.fetchAmenities(params.value),
        { showToast: false }
      ),
      select: (data) => {
        return data as PaginatedResponse<Amenity>
      },
    })
  }

  // Create amenity mutation
  const useCreateAmenityMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<Amenity, AmenityCreateInput>(
        (data) => amenitiesStore.createAmenity(data),
        { 
          successMessage: 'Amenity created successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenities'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Update amenity mutation
  const useUpdateAmenityMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<Amenity, { id: number; data: AmenityUpdateInput }>(
        ({ id, data }) => amenitiesStore.updateAmenity(id, data),
        { 
          successMessage: 'Amenity updated successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenities'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Delete amenity mutation
  const useDeleteAmenityMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<void, number>(
        (id) => amenitiesStore.deleteAmenity(id),
        { 
          successMessage: 'Amenity deleted successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenities'] })
      },
    })
  }

  // Fetch categories query
  const useFetchCategoriesQuery = (params: Ref<CategoriesListParams>) => {
    return useQuery({
      queryKey: ['amenity-categories', params],
      queryFn: queryWrap(
        () => amenitiesStore.fetchCategories(params.value),
        { showToast: false }
      ),
      select: (data) => {
        return data as PaginatedResponse<AmenityCategory>
      },
    })
  }

  // Create category mutation
  const useCreateCategoryMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<AmenityCategory, CategoryCreateInput>(
        (data) => amenitiesStore.createCategory(data),
        { 
          successMessage: 'Category created successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenity-categories'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Update category mutation
  const useUpdateCategoryMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<AmenityCategory, { id: number; data: CategoryUpdateInput }>(
        ({ id, data }) => amenitiesStore.updateCategory(id, data),
        { 
          successMessage: 'Category updated successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenity-categories'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Delete category mutation
  const useDeleteCategoryMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<void, number>(
        (id) => amenitiesStore.deleteCategory(id),
        { 
          successMessage: 'Category deleted successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['amenity-categories'] })
      },
    })
  }

  return {
    useFetchAmenitiesQuery,
    useCreateAmenityMutation,
    useUpdateAmenityMutation,
    useDeleteAmenityMutation,
    useFetchCategoriesQuery,
    useCreateCategoryMutation,
    useUpdateCategoryMutation,
    useDeleteCategoryMutation,
  }
}
