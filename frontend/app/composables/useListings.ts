import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'
import type { Listing, ListingsListParams, ListingStatistics, CreateListingInput } from '../types/listing'
import type { PaginatedResponse } from '../types/api'

export const useListings = () => {
  const listingsStore = useListingsStore()
  const queryClient = useQueryClient()

  // Fetch listings query
  const useFetchListingsQuery = (params: Ref<ListingsListParams>) => {
    return useQuery({
      queryKey: ['listings', params],
      queryFn: queryWrap(
        () => listingsStore.fetchListings(params.value),
        { showToast: false }
      ),
      select: (data) => {
        return data as PaginatedResponse<Listing>
      },
    })
  }

  // Fetch single listing
  const useFetchListingQuery = (id: Ref<number>) => {
    return useQuery({
      queryKey: ['listing', id],
      queryFn: queryWrap(
        () => listingsStore.fetchListing(id.value),
        { showToast: false }
      ),
      enabled: computed(() => !!id.value),
    })
  }

  // Fetch statistics
  const useFetchStatisticsQuery = () => {
    return useQuery({
      queryKey: ['listings-statistics'],
      queryFn: queryWrap(
        () => listingsStore.fetchStatistics(),
        { showToast: false }
      ),
    })
  }

  // Approve listing mutation
  const useApproveListingMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<Listing, number>(
        (id) => listingsStore.approveListing(id),
        { 
          successMessage: 'Listing approved successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })
  }

  // Reject listing mutation
  const useRejectListingMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<Listing, { id: number; reason: string }>(
        ({ id, reason }) => listingsStore.rejectListing(id, reason),
        { 
          successMessage: 'Listing rejected successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  // Publish listing mutation
  const usePublishListingMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<Listing, number>(
        (id) => listingsStore.publishListing(id),
        { 
          successMessage: 'Listing published successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })
  }

  // Archive listing mutation
  const useArchiveListingMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<Listing, number>(
        (id) => listingsStore.archiveListing(id),
        { 
          successMessage: 'Listing archived successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })
  }

  // Delete listing mutation
  const useDeleteListingMutation = () => {
    return useMutation({
      mutationFn: mutationWrap<void, number>(
        (id) => listingsStore.deleteListing(id),
        { 
          successMessage: 'Listing deleted successfully',
          showToast: true,
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })
  }

  // Create listing mutation
  const useCreateListingMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap<Listing, CreateListingInput>(
        (data) => listingsStore.createListing(data),
        { 
          successMessage: 'Listing created successfully',
          showToast: true,
          silentCodes: [422],
        }
      ),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['listings'] })
        queryClient.invalidateQueries({ queryKey: ['listings-statistics'] })
      },
    })

    const { errors, getFieldError } = useMutationErrors(mutation)

    return {
      ...mutation,
      errors,
      getFieldError,
    }
  }

  return {
    useFetchListingsQuery,
    useFetchListingQuery,
    useFetchStatisticsQuery,
    useCreateListingMutation,
    useApproveListingMutation,
    useRejectListingMutation,
    usePublishListingMutation,
    useArchiveListingMutation,
    useDeleteListingMutation,
  }
}
