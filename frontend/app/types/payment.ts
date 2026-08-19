export interface Payment {
  id: number
  reference: string
  amount_minor: number
  amount: number
  currency: string
  status: 'pending' | 'successful' | 'failed' | 'refunded'
  payment_type: string
  payable_type: string
  payable_id: number
  phone?: string
  provider?: string
  created_at: string
  updated_at: string
  user?: { id: number; full_name: string; email: string }
  organization?: { id: number; name: string }
}

export interface PaymentStatistics {
  total: number
  successful: number
  pending: number
  failed: number
  refunded: number
  total_revenue: number
}

export interface PaymentAnalyticsPoint {
  label: string
  value: number
  count?: number
}

export interface PaymentsListParams {
  page?: number
  per_page?: number
  search?: string
  'filter[status]'?: string
  'filter[payment_type]'?: string
  sort?: string
}
