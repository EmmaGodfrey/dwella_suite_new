import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { queryWrap, mutationWrap, useMutationErrors } from '~/utils/queryWrap'
import type { BulkPushInput } from '../types/notification'

export const useNotificationsAdmin = () => {
  const store = useNotificationsAdminStore()
  const queryClient = useQueryClient()

  const useFetchNotificationsQuery = (params: Ref<Record<string, any>>) =>
    useQuery({
      queryKey: ['admin-notifications', params],
      queryFn: queryWrap(() => store.fetchNotifications(params.value), { showToast: false }),
    })

  const useFetchTemplatesQuery = () =>
    useQuery({
      queryKey: ['notification-templates'],
      queryFn: queryWrap(() => store.fetchTemplates(), { showToast: false }),
    })

  const useSendBulkPushMutation = () => {
    const mutation = useMutation({
      mutationFn: mutationWrap(
        (data: BulkPushInput) => store.sendBulkPush(data),
        { successMessage: 'Notification sent successfully', showToast: true, silentCodes: [422] }
      ),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-notifications'] }),
    })
    return { ...mutation, ...useMutationErrors(mutation) }
  }

  return { useFetchNotificationsQuery, useFetchTemplatesQuery, useSendBulkPushMutation }
}
