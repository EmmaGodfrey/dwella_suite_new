export interface Verification {
  id: number
  organization_id: number
  plan_id: number
  status: 'pending' | 'approved' | 'rejected' | 'revoked'
  rejection_reason?: string
  revoke_reason?: string
  submitted_at?: string
  reviewed_at?: string
  created_at: string
  updated_at: string
  organization?: { id: number; name: string; type: string }
  plan?: VerificationPlan
  reviewer?: { id: number; full_name: string }
}

export interface VerificationPlan {
  id: number
  name: string
  price_minor: number
  price: number
  currency: string
  description?: string
  duration_days?: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface VerificationStatistics {
  total: number
  pending: number
  approved: number
  rejected: number
  revoked: number
}

export interface VerificationsListParams {
  page?: number
  per_page?: number
  search?: string
  'filter[status]'?: string
  sort?: string
}

export interface VerificationPlanInput {
  name: string
  price_minor: number
  description?: string
  duration_days?: number
}
