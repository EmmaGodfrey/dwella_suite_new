import { useQuery } from '@tanstack/vue-query'
import { queryWrap } from '~/utils/queryWrap'
import type { PaymentsListParams } from '../types/payment'

export const usePayments = () => {
  const store = usePaymentsStore()

  const useFetchPaymentsQuery = (params: Ref<PaymentsListParams>) =>
    useQuery({
      queryKey: ['payments', params],
      queryFn: queryWrap(() => store.fetchPayments(params.value), { showToast: false }),
    })

  const useFetchPaymentQuery = (id: Ref<number>) =>
    useQuery({
      queryKey: ['payment', id],
      queryFn: queryWrap(() => store.fetchPayment(id.value), { showToast: false }),
      enabled: computed(() => !!id.value),
    })

  const useFetchPaymentStatisticsQuery = () =>
    useQuery({
      queryKey: ['payment-statistics'],
      queryFn: queryWrap(() => store.fetchStatistics(), { showToast: false }),
    })

  const useFetchPaymentAnalyticsQuery = (params: Ref<{ from?: string; to?: string; group_by?: string }>) =>
    useQuery({
      queryKey: ['payment-analytics', params],
      queryFn: queryWrap(() => store.fetchAnalytics(params.value), { showToast: false }),
    })

  return {
    useFetchPaymentsQuery,
    useFetchPaymentQuery,
    useFetchPaymentStatisticsQuery,
    useFetchPaymentAnalyticsQuery,
  }
}
