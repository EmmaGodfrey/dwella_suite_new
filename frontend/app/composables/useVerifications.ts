import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'
import type { VerificationsListParams, VerificationPlanInput } from '../types/verification'

export const useVerifications = () => {
  const store = useVerificationsStore()
  const queryClient = useQueryClient()

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['verifications'] })
    queryClient.invalidateQueries({ queryKey: ['verification-statistics'] })
  }

  const useFetchVerificationsQuery = (params: Ref<VerificationsListParams>) =>
    useQuery({
      queryKey: ['verifications', params],
      queryFn: queryWrap(() => store.fetchVerifications(params.value), { showToast: false }),
    })

  const useFetchVerificationStatisticsQuery = () =>
    useQuery({
      queryKey: ['verification-statistics'],
      queryFn: queryWrap(() => store.fetchStatistics(), { showToast: false }),
    })

  const useFetchVerificationPlansQuery = () =>
    useQuery({
      queryKey: ['verification-plans'],
      queryFn: queryWrap(() => store.fetchPlans(), { showToast: false }),
    })

  const useApproveVerificationMutation = () =>
    useMutation({
      mutationFn: mutationWrap((id: number) => store.approveVerification(id), {
        successMessage: 'Verification approved', showToast: true,
      }),
      onSuccess: invalidate,
    })

  const useRejectVerificationMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, reason }: { id: number; reason: string }) => store.rejectVerification(id, reason),
        { successMessage: 'Verification rejected', showToast: true, silentCodes: [422] }
      ),
      onSuccess: invalidate,
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useRevokeVerificationMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, reason }: { id: number; reason: string }) => store.revokeVerification(id, reason),
        { successMessage: 'Verification revoked', showToast: true, silentCodes: [422] }
      ),
      onSuccess: invalidate,
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useCreatePlanMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap((data: VerificationPlanInput) => store.createPlan(data), {
        successMessage: 'Plan created', showToast: true, silentCodes: [422],
      }),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['verification-plans'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useUpdatePlanMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        ({ id, data }: { id: number; data: Partial<VerificationPlanInput> }) => store.updatePlan(id, data),
        { successMessage: 'Plan updated', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['verification-plans'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  const useDeletePlanMutation = () =>
    useMutation({
      mutationFn: mutationWrap((id: number) => store.deletePlan(id), {
        successMessage: 'Plan deleted', showToast: true,
      }),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['verification-plans'] }),
    })

  return {
    useFetchVerificationsQuery,
    useFetchVerificationStatisticsQuery,
    useFetchVerificationPlansQuery,
    useApproveVerificationMutation,
    useRejectVerificationMutation,
    useRevokeVerificationMutation,
    useCreatePlanMutation,
    useUpdatePlanMutation,
    useDeletePlanMutation,
  }
}
