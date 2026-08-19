import { useQuery } from '@tanstack/vue-query'
import { queryWrap } from '~/utils/queryWrap'
import type { ApplicationsListParams } from '../types/application'

export const useApplications = () => {
  const applicationsStore = useApplicationsStore()

  const useFetchApplicationsQuery = (params: Ref<ApplicationsListParams>) =>
    useQuery({
      queryKey: ['applications', params],
      queryFn: queryWrap(() => applicationsStore.fetchApplications(params.value), { showToast: false }),
    })

  const useFetchApplicationQuery = (id: Ref<number>) =>
    useQuery({
      queryKey: ['application', id],
      queryFn: queryWrap(() => applicationsStore.fetchApplication(id.value), { showToast: false }),
      enabled: computed(() => !!id.value),
    })

  const useFetchApplicationStatisticsQuery = () =>
    useQuery({
      queryKey: ['application-statistics'],
      queryFn: queryWrap(() => applicationsStore.fetchStatistics(), { showToast: false }),
    })

  return {
    useFetchApplicationsQuery,
    useFetchApplicationQuery,
    useFetchApplicationStatisticsQuery,
  }
}
